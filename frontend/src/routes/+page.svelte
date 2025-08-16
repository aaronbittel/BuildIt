<script lang="ts">
	import type { Column } from '$lib/types/board.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let columns = $state(data.columns);

	function handleDragStart(event: DragEvent, itemName: string, sourceKey: string) {
		event.dataTransfer?.setData(
			'application/json',
			JSON.stringify({ itemName: itemName, sourceKey: sourceKey })
		);
	}

	function handleDrop(event: DragEvent, targetKey: string) {
		const raw = event.dataTransfer?.getData('application/json');
		if (!raw) return;
		const { itemName: itemName, sourceKey: sourceKey } = JSON.parse(raw);
		if (sourceKey === targetKey) return;

		addItemToColumn(targetKey, itemName);
		removeItemFromColumn(sourceKey, itemName);
	}

	function removeItemFromColumn(columnKey: string, itemName: string) {
		const column = columns.find((column) => column.key === columnKey);
		if (column !== undefined) {
			column.items = column.items.filter((item) => item !== itemName);
		}
	}

	function addItemToColumn(columnKey: string, itemName: string) {
		const column = columns.find((column) => column.key === columnKey);
		if (column !== undefined) {
			column.items.push(itemName);
		}
	}

	function isHovering(event: DragEvent) {
		const toElement = event.relatedTarget as HTMLElement | null;
		return (
			toElement &&
			event.currentTarget instanceof HTMLElement &&
			event.currentTarget.contains(toElement)
		);
	}
</script>

{#snippet make_column(column: Column)}
	<section
		class="column"
		role="list"
		ondragover={(e) => e.preventDefault()}
		ondrop={(e) => {
			column.isDragover = false;
			handleDrop(e, column.key);
		}}
		ondragenter={(e) => {
			e.preventDefault();
			column.isDragover = true;
		}}
		ondragleave={(e) => {
			if (!isHovering(e)) {
				column.isDragover = false;
			}
		}}
		class:drag-over={column.isDragover}
	>
		<h2 class="column-title">{column.title}</h2>
		<ul class="column-items">
			{#each column.items as item}
				<li
					class="column-item"
					role="listitem"
					draggable="true"
					ondragstart={(e) => handleDragStart(e, item, column.key)}
				>
					{item}
				</li>
			{/each}
		</ul>
	</section>
{/snippet}

<header>
	<h1>My Board</h1>
</header>

<main>
	<div class="board">
		{#each columns as column}
			{@render make_column(column)}
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

	.column {
		display: flex;
		flex-direction: column;
		align-items: center;
		border-radius: 0.3em;
		padding: 1em 0em;
	}

	.column-title {
		font-size: 2em;
		font-weight: bold;
		margin: 0.4em 0 1em;
		border-bottom: 2px solid #7f7faf;
		letter-spacing: 1px;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
		background: rgba(127, 127, 175, 0.2);
		padding: 0.2em 0.5em;
		border-radius: 0.2em;
	}

	.column-items {
		display: flex;
		flex-direction: column;
		width: 100%;
		gap: 1em;
		list-style: none;
		padding: 0.7em;
	}

	.column-item {
		text-align: center;
		padding: 0.5em 0;
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		cursor: grab;
	}

	.column-item:hover {
		background-color: #5a5ab0;
	}

	.column-item:active {
		cursor: grabbing;
	}

	.column.drag-over {
		background-color: rgba(90, 90, 176, 0.3);
	}
</style>
