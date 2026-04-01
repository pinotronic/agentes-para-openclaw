import { useEffect, useRef } from 'react';
import type { Sprite } from '../domain/Sprite';
import type { AtlasConfig } from '../domain/Atlas';
import './AtlasCanvas.css';

interface Props {
  sprites: Sprite[];
  config: AtlasConfig;
  selectedSpriteId: string | null;
}

export function AtlasCanvas({ sprites, config, selectedSpriteId }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imagesRef = useRef<Map<string, HTMLImageElement>>(new Map());

  // Load images
  useEffect(() => {
    sprites.forEach(sprite => {
      if (!imagesRef.current.has(sprite.id)) {
        const img = new Image();
        img.src = sprite.sourceUrl;
        imagesRef.current.set(sprite.id, img);
      }
    });
  }, [sprites]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas with white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, config.width, config.height);

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let x = 0; x < config.width; x += 32) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, config.height);
      ctx.stroke();
    }
    for (let y = 0; y < config.height; y += 32) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(config.width, y);
      ctx.stroke();
    }

    // Draw sprites
    sprites.forEach(sprite => {
      const img = imagesRef.current.get(sprite.id);
      if (img && sprite.packedX !== null && sprite.packedY !== null) {
        ctx.drawImage(img, sprite.packedX, sprite.packedY, sprite.width, sprite.height);

        // Highlight selected sprite
        if (selectedSpriteId === sprite.id) {
          ctx.strokeStyle = '#3b82f6';
          ctx.lineWidth = 2;
          ctx.strokeRect(sprite.packedX, sprite.packedY, sprite.width, sprite.height);
        }
      }
    });

    // Draw atlas border
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, config.width, config.height);
  }, [sprites, config, selectedSpriteId]);

  return (
    <div className="atlas-canvas-container" ref={containerRef}>
      <canvas
        id="atlas-canvas"
        ref={canvasRef}
        width={config.width}
        height={config.height}
        className="atlas-canvas"
      />
      {sprites.length === 0 && (
        <div className="canvas-placeholder">
          <p>Upload images to preview your atlas</p>
        </div>
      )}
    </div>
  );
}
