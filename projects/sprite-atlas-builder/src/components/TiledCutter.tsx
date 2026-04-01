import { useState, useRef, useCallback, useEffect } from 'react';
import './TiledCutter.css';

interface TileSelection {
  col: number;
  row: number;
  name: string;
}

interface PlacedTile {
  id: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  srcX: number;
  srcY: number;
}

export function TiledCutter() {
  const [sourceImage, setSourceImage] = useState<HTMLImageElement | null>(null);
  const [sourceName, setSourceName] = useState<string>('');
  const [sourceWidth, setSourceWidth] = useState<number>(0);
  const [sourceHeight, setSourceHeight] = useState<number>(0);

  const [tileWidth, setTileWidth] = useState<number>(128);
  const [tileHeight, setTileHeight] = useState<number>(128);
  const [cols, setCols] = useState<number>(0);
  const [rows, setRows] = useState<number>(0);

  const [selectedTiles, setSelectedTiles] = useState<TileSelection[]>([]);
  const [isSelecting, setIsSelecting] = useState<boolean>(false);
  const [selectionStart, setSelectionStart] = useState<{col: number, row: number} | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{col: number, row: number} | null>(null);

  const [atlasWidth, setAtlasWidth] = useState<number>(2048);
  const [atlasHeight, setAtlasHeight] = useState<number>(2048);
  const [placedTiles, setPlacedTiles] = useState<PlacedTile[]>([]);
  const [atlasTileSize, setAtlasTileSize] = useState<number>(128);

  // Pan & Zoom state
  const [offsetX, setOffsetX] = useState<number>(0);
  const [offsetY, setOffsetY] = useState<number>(0);
  const [scale, setScale] = useState<number>(1);
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [panStart, setPanStart] = useState<{x: number, y: number} | null>(null);
  const [isSpacePressed, setIsSpacePressed] = useState<boolean>(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const atlasCanvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle paste from clipboard (Ctrl+V)
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            const img = new Image();
            img.onload = () => {
              setSourceImage(img);
              setSourceName(`pasted_image_${Date.now()}.png`);
              setSourceWidth(img.width);
              setSourceHeight(img.height);
              const newCols = Math.floor(img.width / tileWidth);
              const newRows = Math.floor(img.height / tileHeight);
              setCols(newCols);
              setRows(newRows);
            };
            img.src = URL.createObjectURL(file);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [tileWidth, tileHeight]);

  // Handle image load (from file input)
  const handleImageLoad = useCallback((img: HTMLImageElement, fileName: string) => {
    setSourceImage(img);
    setSourceName(fileName);
    setSourceWidth(img.width);
    setSourceHeight(img.height);
    updateGridCalculations(img.width, img.height, tileWidth, tileHeight);
  }, [tileWidth, tileHeight]);

  // Pure function: validates and computes grid dimensions
  const computeGridConfig = (imgW: number, imgH: number, tW: number, tH: number): { cols: number; rows: number } => {
    // Validate inputs
    if (isNaN(imgW) || isNaN(imgH) || isNaN(tW) || isNaN(tH)) {
      console.warn('Invalid dimensions: all values must be valid numbers');
      return { cols: 0, rows: 0 };
    }
    // Prevent division by zero
    if (tW <= 0 || tH <= 0) {
      console.warn('Tile size must be greater than 0');
      return { cols: 0, rows: 0 };
    }
    // Prevent negative dimensions
    if (imgW < 0 || imgH < 0) {
      console.warn('Image dimensions cannot be negative');
      return { cols: 0, rows: 0 };
    }

    const cols = Math.floor(imgW / tW);
    const rows = Math.floor(imgH / tH);
    return { cols, rows };
  };

  const updateGridCalculations = (imgW: number, imgH: number, tW: number, tH: number) => {
    const result = computeGridConfig(imgW, imgH, tW, tH);
    setCols(result.cols);
    setRows(result.rows);
  };

  // Handle file selection
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const img = new Image();
    img.onload = () => handleImageLoad(img, file.name);
    img.src = URL.createObjectURL(file);
  }, [handleImageLoad]);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file || !file.type.startsWith('image/')) return;

    const img = new Image();
    img.onload = () => handleImageLoad(img, file.name);
    img.src = URL.createObjectURL(file);
  }, [handleImageLoad]);

  // Draw source image with grid
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !sourceImage) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to container size for proper scaling
    const container = canvas.parentElement;
    const containerWidth = container?.clientWidth || 800;
    const containerHeight = container?.clientHeight || 600;

    // Calculate scale to fit
    const fitScale = Math.min(
      containerWidth / sourceWidth,
      containerHeight / sourceHeight
    ) * 0.9;

    canvas.width = containerWidth;
    canvas.height = containerHeight;

    // Clear canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply transformations
    ctx.save();
    ctx.translate(canvas.width / 2 + offsetX, canvas.height / 2 + offsetY);
    ctx.scale(scale * fitScale, scale * fitScale);
    ctx.translate(-sourceWidth / 2, -sourceHeight / 2);

    // Draw image
    ctx.drawImage(sourceImage, 0, 0);

    // Draw grid overlay
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
    ctx.lineWidth = 1 / (scale * fitScale);

    // Vertical lines
    for (let x = 0; x <= sourceWidth; x += tileWidth) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, sourceHeight);
      ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= sourceHeight; y += tileHeight) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(sourceWidth, y);
      ctx.stroke();
    }

    // Highlight selected tiles
    ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
    selectedTiles.forEach(tile => {
      ctx.fillRect(tile.col * tileWidth, tile.row * tileHeight, tileWidth, tileHeight);
    });

    // Draw selection rectangle if dragging
    if (selectionStart && selectionEnd) {
      const startCol = Math.min(selectionStart.col, selectionEnd.col);
      const endCol = Math.max(selectionStart.col, selectionEnd.col);
      const startRow = Math.min(selectionStart.row, selectionEnd.row);
      const endRow = Math.max(selectionStart.row, selectionEnd.row);

      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2 / (scale * fitScale);
      ctx.setLineDash([5 / (scale * fitScale), 5 / (scale * fitScale)]);
      ctx.strokeRect(
        startCol * tileWidth,
        startRow * tileHeight,
        (endCol - startCol + 1) * tileWidth,
        (endRow - startRow + 1) * tileHeight
      );
      ctx.setLineDash([]);
    }

    ctx.restore();
  }, [sourceImage, sourceWidth, sourceHeight, tileWidth, tileHeight, selectedTiles, selectionStart, selectionEnd, offsetX, offsetY, scale]);

  // Mouse handlers for pan
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isSpacePressed || e.button === 1) {
      // Middle mouse or space+click = pan
      setIsPanning(true);
      setPanStart({ x: e.clientX - offsetX, y: e.clientY - offsetY });
      e.preventDefault();
      return;
    }

    if (!sourceImage) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const container = canvas.parentElement;
    const containerWidth = container?.clientWidth || 800;
    const containerHeight = container?.clientHeight || 600;

    const fitScale = Math.min(
      containerWidth / sourceWidth,
      containerHeight / sourceHeight
    ) * 0.9;

    // Calculate click position in image coordinates
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;
    const imgX = (canvasX - containerWidth / 2 - offsetX) / (scale * fitScale) + sourceWidth / 2;
    const imgY = (canvasY - containerHeight / 2 - offsetY) / (scale * fitScale) + sourceHeight / 2;

    const col = Math.floor(imgX / tileWidth);
    const row = Math.floor(imgY / tileHeight);

    if (col >= 0 && col < cols && row >= 0 && row < rows) {
      setIsSelecting(true);
      setSelectionStart({ col, row });
      setSelectionEnd({ col, row });
    }
  }, [sourceImage, sourceWidth, sourceHeight, tileWidth, tileHeight, cols, rows, offsetX, offsetY, scale, isSpacePressed]);

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isPanning && panStart) {
      setOffsetX(e.clientX - panStart.x);
      setOffsetY(e.clientY - panStart.y);
      return;
    }

    if (!isSelecting || !sourceImage) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const container = canvas.parentElement;
    const containerWidth = container?.clientWidth || 800;
    const containerHeight = container?.clientHeight || 600;

    const fitScale = Math.min(
      containerWidth / sourceWidth,
      containerHeight / sourceHeight
    ) * 0.9;

    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;
    const imgX = (canvasX - containerWidth / 2 - offsetX) / (scale * fitScale) + sourceWidth / 2;
    const imgY = (canvasY - containerHeight / 2 - offsetY) / (scale * fitScale) + sourceHeight / 2;

    const col = Math.floor(imgX / tileWidth);
    const row = Math.floor(imgY / tileHeight);

    setSelectionEnd({ col: Math.max(0, Math.min(col, cols - 1)), row: Math.max(0, Math.min(row, rows - 1)) });
  }, [isPanning, panStart, isSelecting, sourceImage, sourceWidth, sourceHeight, tileWidth, tileHeight, cols, rows, offsetX, offsetY, scale]);

  const handleCanvasMouseUp = useCallback(() => {
    if (isPanning) {
      setIsPanning(false);
      setPanStart(null);
      return;
    }

    if (!isSelecting || !selectionStart || !selectionEnd) return;

    setIsSelecting(false);

    const startCol = Math.min(selectionStart.col, selectionEnd.col);
    const endCol = Math.max(selectionStart.col, selectionEnd.col);
    const startRow = Math.min(selectionStart.row, selectionEnd.row);
    const endRow = Math.max(selectionStart.row, selectionEnd.row);

    const newTiles: TileSelection[] = [];
    for (let row = startRow; row <= endRow; row++) {
      for (let col = startCol; col <= endCol; col++) {
        newTiles.push({
          col,
          row,
          name: `tile_${col}_${row}`,
        });
      }
    }

    setSelectedTiles(prev => [...prev, ...newTiles]);
    setSelectionStart(null);
    setSelectionEnd(null);
  }, [isPanning, isSelecting, selectionStart, selectionEnd]);

  // Mouse wheel for zoom
  const handleCanvasWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale(prev => Math.max(0.1, Math.min(prev * delta, 10)));
  }, []);

  // Keyboard handlers for space (pan mode)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !isSpacePressed) {
        setIsSpacePressed(true);
      }
      if (e.code === 'KeyR') {
        // Reset view
        setOffsetX(0);
        setOffsetY(0);
        setScale(1);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isSpacePressed]);

  // Draw atlas canvas
  useEffect(() => {
    const canvas = atlasCanvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = atlasWidth;
    canvas.height = atlasHeight;

    // Clear with white/transparent
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, atlasWidth, atlasHeight);

    // Draw placed tiles
    if (sourceImage) {
      placedTiles.forEach(tile => {
        ctx.drawImage(
          sourceImage,
          tile.srcX, tile.srcY, tile.width, tile.height,
          tile.x, tile.y, tile.width, tile.height
        );
      });
    }

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let x = 0; x <= atlasWidth; x += atlasTileSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, atlasHeight);
      ctx.stroke();
    }
    for (let y = 0; y <= atlasHeight; y += atlasTileSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(atlasWidth, y);
      ctx.stroke();
    }

    // Draw border
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, atlasWidth, atlasHeight);
  }, [sourceImage, atlasWidth, atlasHeight, placedTiles, atlasTileSize]);

  // Add selected tiles to atlas
  const addToAtlas = useCallback(() => {
    if (selectedTiles.length === 0) return;

    let currentX = 0;
    let currentY = 0;
    let maxHeightInRow = 0;

    // Find a free position (simple sequential placement)
    const newTiles: PlacedTile[] = selectedTiles.map((tile, index) => {
      const x = currentX;
      const y = currentY;

      currentX += tileWidth;
      maxHeightInRow = Math.max(maxHeightInRow, tileHeight);

      // Wrap to next row if needed
      if (currentX >= atlasWidth) {
        currentX = 0;
        currentY += maxHeightInRow;
        maxHeightInRow = tileHeight;
      }

      return {
        id: `${Date.now()}_${index}`,
        name: tile.name,
        x,
        y,
        width: tileWidth,
        height: tileHeight,
        srcX: tile.col * tileWidth,
        srcY: tile.row * tileHeight,
      };
    });

    setPlacedTiles(prev => [...prev, ...newTiles]);
    setSelectedTiles([]);
  }, [selectedTiles, tileWidth, tileHeight, atlasWidth]);

  const clearSelection = useCallback(() => {
    setSelectedTiles([]);
  }, []);

  const clearAtlas = useCallback(() => {
    setPlacedTiles([]);
  }, []);

  // Export atlas as PNG
  const exportAtlasPNG = useCallback(() => {
    const canvas = atlasCanvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `${sourceName.replace('.png', '')}_atlas.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }, [sourceName]);

  // Export .tsx for Tiled
  const exportTSX = useCallback(() => {
    const tsx = `<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.10.0" name="${sourceName.replace('.png', '')}" tilewidth="${tileWidth}" tileheight="${tileHeight}" columns="${Math.floor(atlasWidth / tileWidth)}">
 <grid offsetx="0" offsety="0"/>
 <tileoffset x="0" y="0"/>
 <transformations/>
 <properties/>
 <image source="${sourceName.replace('.png', '')}_atlas.png" width="${atlasWidth}" height="${atlasHeight}"/>
</tileset>`;

    const blob = new Blob([tsx], { type: 'application/xml' });
    const link = document.createElement('a');
    link.download = `${sourceName.replace('.png', '')}.tsx`;
    link.href = URL.createObjectURL(blob);
    link.click();
  }, [sourceName, tileWidth, tileHeight, atlasWidth, atlasHeight]);

  return (
    <main className="main cutter-mode">
      <aside className="sidebar">
        <div className="config-section">
          <h3>📤 Source Image</h3>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <button onClick={() => fileInputRef.current?.click()}>
            Load Spritesheet
          </button>
          {sourceName && (
            <p className="source-info">
              {sourceName}<br/>
              {sourceWidth} x {sourceHeight} px
            </p>
          )}
        </div>

        <div className="config-section">
          <h3>🔲 Tile Size</h3>
          <label>
            Width: {tileWidth}px
            <input
              type="range"
              min="8"
              max="256"
              value={tileWidth}
              onChange={e => {
                const v = parseInt(e.target.value);
                setTileWidth(v);
                updateGridCalculations(sourceWidth, sourceHeight, v, tileHeight);
              }}
            />
          </label>
          <label>
            Height: {tileHeight}px
            <input
              type="range"
              min="8"
              max="256"
              value={tileHeight}
              onChange={e => {
                const v = parseInt(e.target.value);
                setTileHeight(v);
                updateGridCalculations(sourceWidth, sourceHeight, tileWidth, v);
              }}
            />
          </label>
          {cols > 0 && rows > 0 && (
            <p className="source-info">
              Grid: {cols} x {rows} = {cols * rows} tiles
            </p>
          )}
        </div>

        <div className="config-section">
          <h3>📥 Selection ({selectedTiles.length})</h3>
          <div className="button-group">
            <button onClick={addToAtlas} disabled={selectedTiles.length === 0}>
              Add to Atlas
            </button>
            <button onClick={clearSelection} disabled={selectedTiles.length === 0}>
              Clear
            </button>
          </div>
        </div>

        <div className="config-section">
          <h3>🗺️ Atlas Output</h3>
          <label>
            Atlas Width: {atlasWidth}px
            <input
              type="range"
              min="128"
              max="4096"
              step="128"
              value={atlasWidth}
              onChange={e => setAtlasWidth(parseInt(e.target.value))}
            />
          </label>
          <label>
            Atlas Height: {atlasHeight}px
            <input
              type="range"
              min="128"
              max="4096"
              step="128"
              value={atlasHeight}
              onChange={e => setAtlasHeight(parseInt(e.target.value))}
            />
          </label>
          <label>
            Tile Size: {atlasTileSize}px
            <input
              type="range"
              min="8"
              max="256"
              value={atlasTileSize}
              onChange={e => setAtlasTileSize(parseInt(e.target.value))}
            />
          </label>
          <div className="button-group">
            <button onClick={exportAtlasPNG} disabled={placedTiles.length === 0}>
              Export PNG
            </button>
            <button onClick={exportTSX} disabled={placedTiles.length === 0}>
              Export .tsx
            </button>
            <button onClick={clearAtlas} disabled={placedTiles.length === 0}>
              Clear Atlas
            </button>
          </div>
        </div>
      </aside>

      <section className="canvas-area cutter-area">
        <div className="cutter-panels">
          <div className="source-panel">
            <h3>Source Spritesheet</h3>
            <p>Click and drag to select tiles</p>
            {sourceImage ? (
              <canvas
                ref={canvasRef}
                className={`source-canvas ${isPanning || isSpacePressed ? 'pan-cursor' : ''}`}
                onMouseDown={handleCanvasMouseDown}
                onMouseMove={handleCanvasMouseMove}
                onMouseUp={handleCanvasMouseUp}
                onMouseLeave={handleCanvasMouseUp}
                onWheel={(e) => handleCanvasWheel(e as unknown as WheelEvent)}
              />
            ) : (
              <div
                className="drop-zone"
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
              >
                <p>Drop image here or click Load</p>
              </div>
            )}
          </div>

          <div className="atlas-panel">
            <h3>Atlas Output ({placedTiles.length} tiles)</h3>
            <p>Preview of your atlas</p>
            <canvas ref={atlasCanvasRef} className="atlas-canvas" />
          </div>
        </div>
      </section>
    </main>
  );
}
