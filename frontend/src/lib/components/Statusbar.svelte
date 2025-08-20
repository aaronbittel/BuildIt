<script lang="ts">
	import { fade } from 'svelte/transition';
	import { getStatusbarState } from '$lib/status-bar.svelte';

	const statusbarState = getStatusbarState();
</script>

{#if statusbarState.isShowing}
	<p in:fade out:fade>{statusbarState.message}</p>
{/if}

<style>
	p {
		position: fixed;
		bottom: 1vh;
		left: 50%;
		transform: translateX(-50%);
		width: 80%;
		background: linear-gradient(135deg, #332200, #aa8800, #664400);
		color: #fff8dc;
		padding: 0.4em 0.8em;
		border-radius: 6px;
		text-align: center;
		font-weight: 600;
		font-size: 0.9rem;
		box-shadow: 0 2px 6px rgba(170, 136, 0, 0.4);
	}
</style>
