<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import Statusbar from '$lib/components/Statusbar.svelte';
	import { setStatusbarState } from '$lib/status-bar.svelte';

	let { children } = $props();

	setStatusbarState();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children?.()}

<Statusbar />
