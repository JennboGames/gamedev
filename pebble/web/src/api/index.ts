import type { ApiClient } from './types';
import { liveClient } from './liveClient';

export const api: ApiClient = liveClient;
export type { ApiClient } from './types';
