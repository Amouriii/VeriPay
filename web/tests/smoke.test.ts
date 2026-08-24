import { describe, it, expect } from 'vitest';
import { ROUTES } from '../src/routes';

describe('routes', () => {
  it('exposes a dashboard route', () => {
    expect(ROUTES.dashboard).toBe('/');
  });
});
