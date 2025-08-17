<script lang="ts">
	import type { ColumnType } from '$lib/types';

	type Props = {
		column: ColumnType;
		onDrop: (itemName: string, sourceKey: string, targetKey: string) => void;
	};

	let isDragover = $state(false);

	const { column, onDrop }: Props = $props();

	// let newTaskText = $state('');

	// function hideAddButton(column: ColumnType) {
	// 	column.showAddButton = false;
	// }
	//
	// function showAddButton(column: ColumnType) {
	// 	column.showAddButton = true;
	// }

	function handleDragStart(event: DragEvent, itemName: string, sourceKey: string) {
		event.dataTransfer?.setData(
			'application/json',
			JSON.stringify({ itemName: itemName, sourceKey: sourceKey })
		);
	}

	function handleDropEvent(event: DragEvent) {
		event.preventDefault();
		const raw = event.dataTransfer?.getData('application/json');
		if (!raw) return;
		const { itemName: itemName, sourceKey: sourceKey } = JSON.parse(raw);
		if (sourceKey === column.key) return;

		onDrop(itemName, sourceKey, column.key);
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

<section
	class="column"
	role="list"
	class:drag-over={isDragover}
	ondragover={(e) => {
		e.preventDefault();
	}}
	ondrop={(e) => {
		isDragover = false;
		handleDropEvent(e);
	}}
	ondragenter={(e) => {
		e.preventDefault();
		isDragover = true;
	}}
	ondragleave={(e) => {
		if (!isHovering(e)) {
			isDragover = false;
		}
	}}
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

<style>
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
		width: 100%;
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
</style>
