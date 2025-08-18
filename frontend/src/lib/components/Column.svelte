<script lang="ts">
	import AddTask from './AddTask.svelte';
	import type { StageResponse, TaskResponse } from '$lib/types';

	type Props = {
		stage: StageResponse;
		onDrop: (task: TaskResponse, sourceID: number, targetID: number, toIndex: number) => void;
		onAddItem: (taskName: string) => void;
	};

	let container = $state<HTMLElement | null>(null);
	let isDragover = $state(false);

	const { stage: stage, onDrop, onAddItem }: Props = $props();
	const nameLabel: string = stage.name.charAt(0).toUpperCase();

	function handleDragStart(event: DragEvent, task: TaskResponse, sourceID: number) {
		event.dataTransfer?.setData(
			'application/json',
			JSON.stringify({ task: task, sourceID: sourceID })
		);
	}

	function handleDropEvent(event: DragEvent) {
		event.preventDefault();

		if (!container) return;
		const taskElements = container.querySelectorAll<HTMLElement>('.stage-task');
		const heights = Array.from(taskElements).map((item) => item.offsetTop);

		let i = 0;
		for (; i < heights.length; i++) {
			if (heights[i] >= event.clientY) {
				break;
			}
		}

		const raw = event.dataTransfer?.getData('application/json');
		if (!raw) return;
		const { task: task, sourceID: sourceID } = JSON.parse(raw);
		onDrop(task, sourceID, stage.id, i);
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
	bind:this={container}
	class="stage"
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
	<h2 class="stage-name">
		{stage.name}
		<span class="corner-label">{nameLabel}</span>
	</h2>
	<ul class="stage-tasks">
		{#each stage.tasks as task}
			<li
				class="stage-task"
				role="listitem"
				draggable="true"
				ondragstart={(e) => handleDragStart(e, task, stage.id)}
			>
				{task.name}
			</li>
		{/each}
		<AddTask {nameLabel} {onAddItem} />
	</ul>
</section>

<style>
	.stage {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
		padding: 0.3em;
	}

	.stage-name {
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
		position: relative;
	}

	.corner-label {
		position: absolute;
		top: -0.3em;
		right: -0.3em;
		font-size: 0.5em;
		font-weight: bold;
		color: #fff;
	}

	.stage-tasks {
		width: 100%;
		min-height: 15em;
		display: flex;
		flex-direction: column;
		gap: 1em;
		list-style: none;
		margin: 1em 0 0 0;
	}

	.stage-task {
		text-align: center;
		padding: 0.5em;
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		cursor: grab;
		overflow-wrap: anywhere;
	}

	.stage-task:hover {
		background-color: #5a5ab0;
	}

	.stage-task:active {
		cursor: grabbing;
	}

	.stage.drag-over {
		background-color: rgba(90, 90, 176, 0.3);
	}
</style>
