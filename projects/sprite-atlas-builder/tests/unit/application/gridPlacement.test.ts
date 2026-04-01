import { describe, it, expect } from 'vitest';
import { calculateGridPositions, GridPlacementError } from '../../../src/application/gridPlacement';

describe('Grid Placement', () => {
  it('should place single sprite at origin', () => {
    const sprites = [{ id: '1', name: 'tile.png', width: 32, height: 32 }];
    const positions = calculateGridPositions(sprites, 256, 32, 0);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
  });

  it('should place sprites in a row with correct spacing', () => {
    const sprites = [
      { id: '1', name: 'tile1.png', width: 32, height: 32 },
      { id: '2', name: 'tile2.png', width: 32, height: 32 },
      { id: '3', name: 'tile3.png', width: 32, height: 32 },
    ];
    const positions = calculateGridPositions(sprites, 256, 32, 0);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
    expect(positions.get('2')).toEqual({ x: 32, y: 0 });
    expect(positions.get('3')).toEqual({ x: 64, y: 0 });
  });

  it('should wrap to next row when row is full', () => {
    const sprites = [
      { id: '1', name: 'tile1.png', width: 32, height: 32 },
      { id: '2', name: 'tile2.png', width: 32, height: 32 },
      { id: '3', name: 'tile3.png', width: 32, height: 32 },
    ];
    // atlasWidth=64, tileWidth=32, gap=0 -> 2 per row
    const positions = calculateGridPositions(sprites, 64, 32, 0);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
    expect(positions.get('2')).toEqual({ x: 32, y: 0 });
    expect(positions.get('3')).toEqual({ x: 0, y: 32 }); // wrapped
  });

  it('should apply gap between sprites', () => {
    const sprites = [
      { id: '1', name: 'tile1.png', width: 32, height: 32 },
      { id: '2', name: 'tile2.png', width: 32, height: 32 },
    ];
    const gap = 2;
    const positions = calculateGridPositions(sprites, 256, 32, gap);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
    expect(positions.get('2')).toEqual({ x: 34, y: 0 }); // 32 + 2 gap
  });

  it('should throw when sprite does not fit in atlas width', () => {
    const sprites = [{ id: '1', name: 'tile.png', width: 128, height: 32 }];
    
    expect(() => calculateGridPositions(sprites, 64, 32, 0))
      .toThrow(GridPlacementError);
  });

  it('should handle sprites of different widths', () => {
    const sprites = [
      { id: '1', name: 'small.png', width: 16, height: 32 },
      { id: '2', name: 'large.png', width: 64, height: 32 },
    ];
    const positions = calculateGridPositions(sprites, 256, 32, 0);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
    expect(positions.get('2')).toEqual({ x: 16, y: 0 });
  });

  it('should handle empty sprite array', () => {
    const positions = calculateGridPositions([], 256, 32, 0);
    expect(positions.size).toBe(0);
  });

  it('should calculate correct row count', () => {
    const sprites = [
      { id: '1', name: 'tile.png', width: 32, height: 32 },
      { id: '2', name: 'tile.png', width: 32, height: 32 },
      { id: '3', name: 'tile.png', width: 32, height: 32 },
      { id: '4', name: 'tile.png', width: 32, height: 32 },
      { id: '5', name: 'tile.png', width: 32, height: 32 },
    ];
    // atlasWidth=64, tileWidth=32 -> 2 per row, 5 sprites -> 3 rows
    const positions = calculateGridPositions(sprites, 64, 32, 0);

    expect(positions.get('1')).toEqual({ x: 0, y: 0 });
    expect(positions.get('2')).toEqual({ x: 32, y: 0 });
    expect(positions.get('3')).toEqual({ x: 0, y: 32 });
    expect(positions.get('4')).toEqual({ x: 32, y: 32 });
    expect(positions.get('5')).toEqual({ x: 0, y: 64 });
  });
});
