<script lang="ts">
	import type { PageProps } from './$types';
	import Column from '$lib/components/Column.svelte';

	let { data }: PageProps = $props();
	let columns = $state(data.columns);

	function onDrop(itemName: string, sourceKey: string, targetKey: string) {
		if (sourceKey === targetKey) return;

		const source = columns.find((c) => c.key === sourceKey);
		const target = columns.find((c) => c.key === targetKey);

		if (source && target) {
			source.items = source.items.filter((item: string) => item !== itemName);
			target.items.push(itemName);
		}
	}
</script>

<header>
	<h1>My Board</h1>
</header>

<main>
	<div class="board">
		{#each columns as column}
			<Column {column} {onDrop} />
		{/each}
	</div>
</main>

<style>
	:global(*) {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
	}

	:global(body) {
		min-height: 100vh;
		background: linear-gradient(135deg, #16161b, #23233a, #3a3360);
		color: #f0f0f0;
		font-family: sans-serif;
	}

	header {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 100px;
		margin-bottom: 2em;
	}

	main {
		display: grid;
		grid-template-columns: 7% 1fr 7%;
		grid-template-areas: '. board .';
	}

	.board {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 4em;
		grid-area: board;
	}

	@media (max-width: 1200px) {
		main {
			grid-template-columns: 3% 1fr 3%;
		}

		.board {
			gap: 2em;
		}
	}
</style>
