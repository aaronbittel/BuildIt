<script lang="ts">
	import AddTask from './AddTask.svelte';
	import type { StageResponse, TaskResponse } from '$lib/types';
	import { updateTaskNameRequest } from '$lib/api';
	import { tick } from 'svelte';

	type Props = {
		stage: StageResponse;
		onDrop: (task: TaskResponse, sourceID: number, targetID: number, toIndex: number) => void;
		onAddItem: (taskName: string) => void;
		updateTaskName: (stage: StageResponse, idx: number, newName: string) => void;
	};

	let container = $state<HTMLElement | null>(null);
	let editingIdx: number | null = $state(null);
	let isDragover = $state(false);

	const { stage, onDrop, onAddItem, updateTaskName }: Props = $props();
	const nameLabel: string = stage.name.charAt(0).toUpperCase();

	let textarea: HTMLTextAreaElement | null = $state(null);

	function resizeTextarea() {
		if (!textarea) return;
		textarea.style.height = 'auto';
		textarea.style.height = textarea.scrollHeight + 'px';
	}
	$effect(() => {
		resizeTextarea();
	});

	async function handleDoubleClick(idx: number) {
		if (editingIdx !== null) {
			const prev_task = stage.tasks[editingIdx];
			const updated_task = await updateTaskNameRequest(prev_task.id, prev_task.name);
			updateTaskName(stage, editingIdx, updated_task.name);
		}
		// save the changes to the previous editing
		editingIdx = idx;
		await tick();
		textarea?.focus();
	}

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

	async function handleBlur() {
		if (editingIdx === null) return;
		const prev_task = stage.tasks[editingIdx];
		const updated_task = await updateTaskNameRequest(prev_task.id, prev_task.name);
		updateTaskName(stage, editingIdx, updated_task.name);
		editingIdx = null;
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
		{#each stage.tasks as task, idx}
			{#if idx == editingIdx}
				<!-- FIXME: id -->
				<textarea
					id={`${nameLabel}-textarea`}
					bind:this={textarea}
					bind:value={task.name}
					onfocus={() => (editingIdx = idx)}
					onblur={() => handleBlur()}
				></textarea>
			{:else}
				<li
					class="stage-task"
					role="listitem"
					draggable="true"
					ondragstart={(e) => handleDragStart(e, task, stage.id)}
					ondblclick={() => handleDoubleClick(idx)}
				>
					{task.name}
				</li>
			{/if}
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

	textarea {
		font-family: inherit;
		color: inherit;
		line-height: 1.2;
		background: rgba(127, 127, 175, 0.2);
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.5em;
		overflow: hidden;
		resize: none;
	}
</style>
