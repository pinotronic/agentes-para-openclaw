import { describe, it, expect } from 'vitest';
import { createSprite, validateSpriteDimensions } from '../../../src/domain/Sprite';
import type { Sprite } from '../../../src/domain/Sprite';

describe('Sprite Entity', () => {
  it('should create a sprite with correct properties', () => {
    const sprite = createSprite({
      id: '1',
      name: 'player_idle_01.png',
      width: 32,
      height: 32,
      sourceUrl: '/uploads/player_idle_01.png',
      metadata: { format: 'PNG', originalSize: 1024 },
    });

    expect(sprite.id).toBe('1');
    expect(sprite.name).toBe('player_idle_01.png');
    expect(sprite.width).toBe(32);
    expect(sprite.height).toBe(32);
    expect(sprite.isPacked).toBe(false);
    expect(sprite.packedX).toBeNull();
    expect(sprite.packedY).toBeNull();
  });

  it('should mark sprite as packed when coordinates are set', () => {
    const sprite = createSprite({
      id: '1',
      name: 'player_idle_01.png',
      width: 32,
      height: 32,
      sourceUrl: '/uploads/player_idle_01.png',
      metadata: { format: 'PNG', originalSize: 1024 },
    });

    sprite.packedX = 0;
    sprite.packedY = 0;
    sprite.isPacked = true;
    sprite.gridIndex = 0;

    expect(sprite.isPacked).toBe(true);
    expect(sprite.packedX).toBe(0);
    expect(sprite.packedY).toBe(0);
    expect(sprite.gridIndex).toBe(0);
  });

  it('should support different image formats', () => {
    const formats: Sprite['metadata']['format'][] = ['PNG', 'JPEG', 'WEBP'];

    formats.forEach((format) => {
      const sprite = createSprite({
        id: '1',
        name: 'test.png',
        width: 32,
        height: 32,
        sourceUrl: '/uploads/test.png',
        metadata: { format, originalSize: 512 },
      });
      expect(sprite.metadata.format).toBe(format);
    });
  });

  it('should reject negative dimensions via validateSpriteDimensions', () => {
    expect(() => validateSpriteDimensions(-1, 32)).toThrow('Width must be positive');
  });

  it('should reject zero dimensions via validateSpriteDimensions', () => {
    expect(() => validateSpriteDimensions(32, 0)).toThrow('Height must be positive');
  });

  it('should reject negative height via createSprite', () => {
    expect(() =>
      createSprite({
        id: '1',
        name: 'test.png',
        width: 32,
        height: -1,
        sourceUrl: '/uploads/test.png',
        metadata: { format: 'PNG', originalSize: 512 },
      })
    ).toThrow('Height must be positive');
  });
});
