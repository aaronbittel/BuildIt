import { writable } from 'svelte/store';

export const statusMessage = writable<string | null>(null);
export const isDragging = writable(false);
