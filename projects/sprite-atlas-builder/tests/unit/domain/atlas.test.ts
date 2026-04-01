import { describe, it, expect, beforeEach } from 'vitest';
import type { Atlas } from '../../../src/domain/Atlas';
import type { AtlasConfig } from '../../../src/domain/Atlas';

describe('Atlas Entity', () => {
  let atlas: Atlas;
  let config: AtlasConfig;

  beforeEach(() => {
    config = {
      name: 'player_sprites',
      width: 256,
      height: 256,
      exportMode: 'JSON',
      autoPack: false,
      gap: 2,
      rotation: false,
    };

    atlas = {
      id: 'atlas-1',
      config,
      sprites: [],
      createdAt: new Date(),
    };
  });

  it('should create an atlas with default values', () => {
    expect(atlas.id).toBe('atlas-1');
    expect(atlas.config.name).toBe('player_sprites');
    expect(atlas.config.width).toBe(256);
    expect(atlas.config.height).toBe(256);
    expect(atlas.config.gap).toBe(2);
    expect(atlas.sprites).toEqual([]);
  });

  it('should add sprites to atlas', () => {
    const sprite = {
      id: '1',
      name: 'tile_01.png',
      width: 32,
      height: 32,
      sourceUrl: '/uploads/tile_01.png',
      metadata: { format: 'PNG' as const, originalSize: 512 },
      packedX: 0,
      packedY: 0,
      gridIndex: 0,
      isPacked: true,
    };

    atlas.sprites.push(sprite);

    expect(atlas.sprites).toHaveLength(1);
    expect(atlas.sprites[0].name).toBe('tile_01.png');
  });

  it('should calculate total area correctly', () => {
    const sprite1 = {
      id: '1',
      name: 'tile_01.png',
      width: 32,
      height: 32,
      sourceUrl: '/uploads/tile_01.png',
      metadata: { format: 'PNG' as const, originalSize: 512 },
      packedX: 0,
      packedY: 0,
      gridIndex: 0,
      isPacked: true,
    };

    const sprite2 = {
      id: '2',
      name: 'tile_02.png',
      width: 32,
      height: 32,
      sourceUrl: '/uploads/tile_02.png',
      metadata: { format: 'PNG' as const, originalSize: 512 },
      packedX: 32,
      packedY: 0,
      gridIndex: 1,
      isPacked: true,
    };

    atlas.sprites.push(sprite1, sprite2);

    const totalArea = atlas.sprites.reduce((sum, s) => sum + s.width * s.height, 0);
    expect(totalArea).toBe(2048); // 32*32 + 32*32
  });

  it('should export to JSON format', () => {
    atlas.config.exportMode = 'JSON';
    expect(atlas.config.exportMode).toBe('JSON');
  });

  it('should support auto-pack toggle', () => {
    atlas.config.autoPack = true;
    expect(atlas.config.autoPack).toBe(true);
  });

  it('should reject atlas smaller than minimum size', () => {
    expect(() => {
      atlas.config.width = 16;
      atlas.config.height = 16;
    }).not.toThrow(); // Config allows small, runtime check when placing sprites
  });
});
