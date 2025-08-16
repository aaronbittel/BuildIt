<script lang="ts">
	import type { Column } from '$lib/types/board.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let columns = $state(data.columns);
	let newTaskText = $state('');

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

	function hideAddButton(column: Column) {
		column.showAddButton = false;
	}

	function showAddButton(column: Column) {
		column.showAddButton = true;
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
		{#if column.showAddButton}
			<button class="btn-add-card" onclick={() => hideAddButton(column)}>
				<svg viewBox="0 0 24 24">
					<path
						d="M12 5v14m-7-7h14"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
					/>
				</svg>
				Add another Card
			</button>
		{:else}
			<div class="add-task">
				<textarea bind:value={newTaskText} placeholder="New task"></textarea>
				<button onclick={() => showAddButton(column)}>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						fill="currentColor"
						viewBox="0 0 16 16"
					>
						<path d="M8 4v8m4-4H4" />
					</svg>
					Add
				</button>
			</div>
		{/if}
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
		width: 100%;
		padding: 0.7em;
	}

	.column-title {
		width: 100%;
		font-size: 2em;
		font-weight: bold;
		border-bottom: 2px solid #7f7faf;
		letter-spacing: 1px;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
		background: rgba(127, 127, 175, 0.2);
		padding: 0.2em 0.5em;
		border-radius: 0.2em;
		display: flex;
		justify-content: center;
	}

	.column-items {
		display: flex;
		flex-direction: column;
		gap: 1em;
		list-style: none;
		margin: 1em 0 0 0;
	}

	/* if the column is empty, keep the 'add'-btn higher up*/
	.column-items li:last-of-type {
		margin-bottom: 1em;
	}

	.column-item {
		text-align: center;
		padding: 0.5em;
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

	.btn-add-card {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5em;
		background-color: rgba(127, 127, 175, 0.3);
		color: #f0f0f0;
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.4em 0.6em;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-add-card:hover {
		background-color: rgba(127, 127, 175, 0.5);
		border-color: #5a5ab0;
	}

	.btn-add-card:active {
		background-color: rgba(90, 90, 176, 0.6);
		transform: translateY(1px);
	}

	.btn-add-card svg {
		width: 1em;
		height: 1em;
		fill: currentColor;
	}

	.add-task {
		display: flex;
		flex-direction: column;
		gap: 0.5em;
		margin-top: 1em;
		width: 100%;
	}

	.add-task textarea {
		font-family: inherit;
		color: inherit;
		line-height: 1.2;
		background: rgba(127, 127, 175, 0.2);
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.5em;
	}

	.add-task textarea::placeholder {
		color: #dcdcff;
	}

	.add-task button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.3em;
		padding: 0.4em 0.8em;
		background-color: #7f7faf;
		border: none;
		border-radius: 0.5em;
		cursor: pointer;
		color: #f0f0f0;
		font-weight: bold;
		transition: background-color 0.2s;
	}

	.add-task button:hover {
		background-color: #5a5ab0;
	}

	.add-task button svg {
		fill: currentColor;
	}
</style>
