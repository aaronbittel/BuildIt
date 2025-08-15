<script lang="ts">
	type Column = {
		key: string;
		title: string;
		items: string[];
		isDragover: boolean;
	};

	let columns: Column[] = $state([
		{
			key: 'backlog',
			title: 'Backlog',
			items: [
				'Order of item depends on drag position',
				'create a backend',
				'move the title out from the item-columns',
				'add more metadata to the tasks',
				'add button for creating new tasks'
			],
			isDragover: false
		},
		{
			key: 'in_progress',
			title: 'In Progress',
			items: ['styling', 'learning css and html things', 'first time using typescript'],
			isDragover: false
		},
		{
			key: 'done',
			title: 'Done',
			items: [
				'first setup for the page',
				'setting up nvim for svelte and typescript',
				'kinda working board',
				'items are draggable between columns',
				'nice visual'
			],
			isDragover: false
		}
	]);

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

<header>
	<h1>My Board</h1>
</header>

{#snippet make_column(column: Column)}
	<div
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
		<div class="column-title">{column.title}</div>
		<div class="column-items">
			{#each column.items as item}
				<div
					class="column-item"
					role="listitem"
					draggable="true"
					ondragstart={(e) => handleDragStart(e, item, column.key)}
				>
					{item}
				</div>
			{/each}
		</div>
	</div>
{/snippet}

<div class="board">
	{#each columns as column}
		{@render make_column(column)}
	{/each}
</div>

<style>
	:global(html, body) {
		height: 100%;
		margin: 0;
		padding: 0;
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
	}

	.board {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1em;
		padding: 1em;
	}

	.column {
		display: flex;
		flex-direction: column;
		background-color: #2a2a3d;
		align-items: center;
		outline: 2px solid #a0a0c0;
		border-radius: 0.3em;
	}

	.column-title {
		font-size: 2em;
		font-weight: bold;
		margin: 0.4em 0em 1em 0em;
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
		align-items: stretch;
		gap: 1em;
		padding-bottom: 0.7em;
	}

	.column-item {
		text-align: center;
		flex: 1 1 auto;
		padding: 0.5em 0.7em;
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		margin: 0em 1em;
	}

	.column-item:hover {
		cursor: grab;
		background-color: #5a5ab0;
	}

	.column-item:active {
		cursor: grabbing;
	}

	.column.drag-over {
		background-color: rgba(90, 90, 176, 0.3);
	}
</style>
