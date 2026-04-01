import { describe, it, expect } from 'vitest';
import { validateSpriteDimensions } from '../../../src/domain/Sprite';
import { validateAtlasConfig, MAX_FILE_SIZE, MAX_BATCH_SIZE } from '../../../src/domain/validation';

describe('Validation', () => {
  describe('validateSpriteDimensions', () => {
    it('should accept valid positive dimensions', () => {
      expect(() => validateSpriteDimensions(32, 32)).not.toThrow();
      expect(() => validateSpriteDimensions(1, 1)).not.toThrow();
      expect(() => validateSpriteDimensions(4096, 4096)).not.toThrow();
    });

    it('should reject width of zero', () => {
      expect(() => validateSpriteDimensions(0, 32)).toThrow('Width must be positive');
    });

    it('should reject height of zero', () => {
      expect(() => validateSpriteDimensions(32, 0)).toThrow('Height must be positive');
    });

    it('should reject negative dimensions', () => {
      expect(() => validateSpriteDimensions(-1, 32)).toThrow('Width must be positive');
      expect(() => validateSpriteDimensions(32, -1)).toThrow('Height must be positive');
    });

    it('should accept decimal dimensions (valid positive numbers)', () => {
      // Decimals > 0 are valid (sub-pixel rendering possible)
      expect(() => validateSpriteDimensions(32.5, 32)).not.toThrow();
      expect(() => validateSpriteDimensions(32, 32.5)).not.toThrow();
    });
  });

  describe('validateAtlasConfig', () => {
    it('should accept valid config', () => {
      const validConfig = {
        name: 'test_atlas',
        width: 256,
        height: 256,
        exportMode: 'PNG' as const,
        autoPack: false,
        gap: 2,
        rotation: false,
      };
      expect(() => validateAtlasConfig(validConfig)).not.toThrow();
    });

    it('should reject width smaller than minimum', () => {
      const config = {
        name: 'test_atlas',
        width: 8, // min is 16
        height: 256,
        exportMode: 'PNG' as const,
        autoPack: false,
        gap: 2,
        rotation: false,
      };
      expect(() => validateAtlasConfig(config)).toThrow();
    });

    it('should reject width larger than maximum', () => {
      const config = {
        name: 'test_atlas',
        width: 8192, // max is 4096
        height: 256,
        exportMode: 'PNG' as const,
        autoPack: false,
        gap: 2,
        rotation: false,
      };
      expect(() => validateAtlasConfig(config)).toThrow();
    });

    it('should reject negative gap', () => {
      const config = {
        name: 'test_atlas',
        width: 256,
        height: 256,
        exportMode: 'PNG' as const,
        autoPack: false,
        gap: -1,
        rotation: false,
      };
      expect(() => validateAtlasConfig(config)).toThrow('Gap must be non-negative');
    });
  });

  describe('File size constants', () => {
    it('should have correct MAX_FILE_SIZE (10MB)', () => {
      expect(MAX_FILE_SIZE).toBe(10 * 1024 * 1024);
    });

    it('should have correct MAX_BATCH_SIZE (50MB)', () => {
      expect(MAX_BATCH_SIZE).toBe(50 * 1024 * 1024);
    });
  });
});
