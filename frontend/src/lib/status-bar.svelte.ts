import { getContext, onDestroy, setContext } from 'svelte';

class StatusBar {
	message = $state<string>('');
	isShowing = $state(true);
	timeout: number | null = null;

	constructor() {
		onDestroy(() => {
			if (this.timeout !== null) clearTimeout(this.timeout);
		});
	}

	show(message: string, durationMS: number = 1500) {
		if (this.timeout !== null) clearTimeout(this.timeout);
		this.message = message;
		this.isShowing = true;
		this.timeout = setTimeout(() => {
			message = '';
			this.isShowing = false;
		}, durationMS);
	}
}

const STATUS_KEY = Symbol('STATUS');

function setStatusbarState() {
	return setContext(STATUS_KEY, new StatusBar());
}

function getStatusbarState() {
	return getContext<ReturnType<typeof setStatusbarState>>(STATUS_KEY);
}

export { StatusBar, setStatusbarState, getStatusbarState };
