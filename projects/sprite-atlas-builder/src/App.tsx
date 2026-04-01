import { useState, useCallback } from 'react';
import { ImageUploader } from './components/ImageUploader';
import { AtlasCanvas } from './components/AtlasCanvas';
import { TiledCutter } from './components/TiledCutter';
import type { AtlasConfig } from './domain/Atlas';
import type { Sprite } from './domain/Sprite';
import { calculateGridPositions } from './application/gridPlacement';
import './App.css';

type Mode = 'builder' | 'cutter';

const DEFAULT_CONFIG: AtlasConfig = {
  name: 'sprites',
  width: 256,
  height: 256,
  exportMode: 'PNG',
  autoPack: false,
  gap: 0,
  rotation: false,
};

export default function App() {
  const [mode, setMode] = useState<Mode>('builder');
  const [sprites, setSprites] = useState<Sprite[]>([]);
  const [config, setConfig] = useState<AtlasConfig>(DEFAULT_CONFIG);
  const [selectedSpriteId, setSelectedSpriteId] = useState<string | null>(null);

  const handleImagesLoaded = useCallback((loadedSprites: Sprite[]) => {
    setSprites(prev => [...prev, ...loadedSprites]);
  }, []);

  const handleRemoveSprite = useCallback((id: string) => {
    setSprites(prev => prev.filter(s => s.id !== id));
    if (selectedSpriteId === id) setSelectedSpriteId(null);
  }, [selectedSpriteId]);

  const handleClearAll = useCallback(() => {
    setSprites([]);
    setSelectedSpriteId(null);
  }, []);

  const gridPositions = (() => {
    try {
      return calculateGridPositions(
        sprites.map(s => ({ id: s.id, name: s.name, width: s.width, height: s.height })),
        config.width,
        config.gap > 0 ? 32 : 32,
        config.gap
      );
    } catch {
      // If sprites don't fit, return empty positions
      return new Map<string, { x: number; y: number }>();
    }
  })();

  const packedSprites = sprites.map(sprite => ({
    ...sprite,
    packedX: gridPositions.get(sprite.id)?.x ?? null,
    packedY: gridPositions.get(sprite.id)?.y ?? null,
  }));

  const handleExportPNG = () => {
    const canvas = document.getElementById('atlas-canvas') as HTMLCanvasElement;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `${config.name}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  const handleExportJSON = () => {
    const jsonData = packedSprites.map(sprite => ({
      name: sprite.name,
      x: sprite.packedX ?? 0,
      y: sprite.packedY ?? 0,
      width: sprite.width,
      height: sprite.height,
    }));
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.download = `${config.name}.json`;
    link.href = URL.createObjectURL(blob);
    link.click();
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎨 Sprite Atlas Builder</h1>
        <div className="mode-selector">
          <button
            className={mode === 'builder' ? 'active' : ''}
            onClick={() => setMode('builder')}
          >
            Builder Mode
          </button>
          <button
            className={mode === 'cutter' ? 'active' : ''}
            onClick={() => setMode('cutter')}
          >
            Tiled Cutter
          </button>
        </div>
      </header>

      {mode === 'builder' && (
        <BuilderMode
          sprites={sprites}
          config={config}
          selectedSpriteId={selectedSpriteId}
          packedSprites={packedSprites}
          onImagesLoaded={handleImagesLoaded}
          onRemoveSprite={handleRemoveSprite}
          onClearAll={handleClearAll}
          onConfigChange={setConfig}
          onSelectSprite={setSelectedSpriteId}
          onExportPNG={handleExportPNG}
          onExportJSON={handleExportJSON}
        />
      )}

      {mode === 'cutter' && <TiledCutter />}
    </div>
  );
}

// Builder Mode Component
interface BuilderProps {
  sprites: Sprite[];
  config: AtlasConfig;
  selectedSpriteId: string | null;
  packedSprites: Sprite[];
  onImagesLoaded: (sprites: Sprite[]) => void;
  onRemoveSprite: (id: string) => void;
  onClearAll: () => void;
  onConfigChange: (config: AtlasConfig) => void;
  onSelectSprite: (id: string | null) => void;
  onExportPNG: () => void;
  onExportJSON: () => void;
}

function BuilderMode({
  sprites,
  config,
  selectedSpriteId,
  packedSprites,
  onImagesLoaded,
  onRemoveSprite,
  onClearAll,
  onConfigChange,
  onSelectSprite,
  onExportPNG,
  onExportJSON,
}: BuilderProps) {
  return (
    <main className="main">
      <aside className="sidebar">
        <ImageUploader onImagesLoaded={onImagesLoaded} />

        <div className="config-section">
          <h3>Atlas Config</h3>
          <label>
            Name:
            <input
              type="text"
              value={config.name}
              onChange={e => onConfigChange({ ...config, name: e.target.value })}
            />
          </label>
          <label>
            Width:
            <input
              type="number"
              value={config.width}
              onChange={e => onConfigChange({ ...config, width: parseInt(e.target.value) || 256 })}
              min={16}
              max={4096}
            />
          </label>
          <label>
            Height:
            <input
              type="number"
              value={config.height}
              onChange={e => onConfigChange({ ...config, height: parseInt(e.target.value) || 256 })}
              min={16}
              max={4096}
            />
          </label>
          <label>
            Gap:
            <input
              type="number"
              value={config.gap}
              onChange={e => onConfigChange({ ...config, gap: parseInt(e.target.value) || 0 })}
              min={0}
              max={32}
            />
          </label>
        </div>

        {sprites.length > 0 && (
          <div className="sprite-list">
            <h3>Sprites ({sprites.length})</h3>
            {sprites.map(sprite => (
              <div
                key={sprite.id}
                className={`sprite-item ${selectedSpriteId === sprite.id ? 'selected' : ''}`}
                onClick={() => onSelectSprite(sprite.id)}
              >
                <span className="sprite-name">{sprite.name}</span>
                <span className="sprite-size">{sprite.width}x{sprite.height}</span>
                <button
                  className="remove-btn"
                  onClick={e => {
                    e.stopPropagation();
                    onRemoveSprite(sprite.id);
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </aside>

      <section className="canvas-area">
        <div className="controls">
          <button onClick={onClearAll} disabled={sprites.length === 0}>Clear All</button>
          <button onClick={onExportPNG} disabled={sprites.length === 0}>Export PNG</button>
          <button onClick={onExportJSON} disabled={sprites.length === 0}>Export JSON</button>
        </div>
        <AtlasCanvas sprites={packedSprites} config={config} selectedSpriteId={selectedSpriteId} />
      </section>
    </main>
  );
}
