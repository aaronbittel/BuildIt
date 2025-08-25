<script lang="ts">
	import type { StageResponse, TaskResponse } from '$lib/types';
	import { updateTaskNameRequest } from '$lib/api';
	import { tick } from 'svelte';
	import { isDragging } from '$lib/store';
	import AddTask from './AddTask.svelte';
	import { INACTIVE } from '$lib/utils';
	import { getStagesState } from '$lib/stages.svelte';
	import { enhance } from '$app/forms';

	type Props = {
		stage: StageResponse;
		onDrop: (task: TaskResponse, sourceID: number, targetID: number) => void;
		updateTaskName: (stage: StageResponse, idx: number, newName: string) => void;
		cornerLabel: string;
	};

	let container = $state<HTMLElement | null>(null);
	let editingIdx: number | null = $state(null);
	let isDragover = $state(false);

	const { stage, onDrop, updateTaskName, cornerLabel }: Props = $props();

	let stageName = $state(stage.name);

	const stagesState = getStagesState();

	let textarea: HTMLTextAreaElement | null = $state(null);

	function resizeTextarea(textarea: HTMLTextAreaElement | null) {
		if (!textarea) return;
		textarea.style.height = 'auto';
		textarea.style.height = textarea.scrollHeight + 'px';
	}

	// FIXME: Does not work
	$effect(() => {
		resizeTextarea(textarea);
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

	function handleDragStartTask(event: DragEvent, task: TaskResponse) {
		isDragging.set(true);
		event.stopPropagation(); // so stages' onDragStart does not override this
		event.dataTransfer?.setData('application/json', JSON.stringify({ type: 'task', task: task }));
	}

	function handleOnStageDrop(event: DragEvent) {
		event.preventDefault();
		const raw = event.dataTransfer?.getData('application/json');
		if (!raw) return;

		const { type } = JSON.parse(raw) as { type: string };
		if (type !== 'task') return;

		if (!container) return;
		const taskElements = container.querySelectorAll<HTMLElement>('.stage-task');
		const heights = Array.from(taskElements).map((item) => item.offsetTop);

		// FIXME: This is still pretty buggy
		let i = 0;
		for (; i < heights.length; i++) {
			if (heights[i] >= event.clientY) {
				break;
			}
		}

		const { task } = JSON.parse(raw);
		onDrop(task, stage.id, i);
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

	function handleDragStartStage(event: DragEvent, stageID: number) {
		isDragging.set(true);

		event.dataTransfer?.setData('application/json', JSON.stringify({ type: 'stage', stageID }));
	}
</script>

<section
	bind:this={container}
	class="stage"
	role="list"
	class:drag-over={isDragover}
	draggable="true"
	ondragstart={(e) => handleDragStartStage(e, stage.id)}
	ondragend={() => isDragging.set(false)}
	ondragover={(e) => {
		e.preventDefault();
	}}
	ondrop={(e) => {
		isDragover = false;
		handleOnStageDrop(e);
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
	{#if stage.id === INACTIVE}
		<div class="stage-header">
			<form
				method="POST"
				action="?/addStage"
				use:enhance={() => {
					return async ({ result, update }) => {
						if (result.type === 'success') {
							stagesState.updateStage(stage.id, result.data?.data as StageResponse);
						}
						update();
					};
				}}
			>
				<input name="name" class="stage-name-input" bind:value={stageName} placeholder="Default" />
			</form>
		</div>
	{:else}
		<div class="stage-header">
			<h2 class="stage-name">{stage.name}</h2>
			<span class="corner-label">{cornerLabel}</span>
		</div>
		<ul class="stage-tasks">
			{#each stage.tasks as task, idx}
				{#if idx == editingIdx}
					<!-- FIXME: id -->
					<textarea
						id={`${cornerLabel}-textarea`}
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
						ondragstart={(e) => handleDragStartTask(e, task)}
						ondragend={() => isDragging.set(false)}
						ondblclick={() => handleDoubleClick(idx)}
					>
						{task.name}
					</li>
				{/if}
			{/each}
			<AddTask {cornerLabel} stageID={stage.id} />
		</ul>
	{/if}
</section>

<style>
	.stage {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
		padding: 0.3em;
	}

	.stage-header {
		position: relative;
		width: 100%;
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
		text-align: center;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.corner-label {
		position: absolute;
		top: -0.3em;
		right: -0.3em;
		font-size: 1em;
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

	.stage-name-input {
		width: 100%;
		font-size: 2em;
		font-weight: bold;
		border: none;
		border: 2px dashed #7f7faf;
		letter-spacing: 1px;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
		background: rgba(127, 127, 175, 0.15);
		padding: 0.2em 0.5em;
		border-radius: 0.2em;
		text-align: center;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		color: inherit;
		font-family: inherit;
		outline: none;
		transition: all 0.2s ease;
		cursor: text;
	}

	.stage-name-input::placeholder {
		color: rgba(127, 127, 175, 0.6);
		font-style: italic;
	}

	.stage-name-input:hover {
		background: rgba(127, 127, 175, 0.22);
	}

	.stage-name-input:focus {
		border: 2px solid #7f7faf;
		box-shadow: 0 2px 8px rgba(127, 127, 175, 0.4);
		background: rgba(127, 127, 175, 0.3);
	}

	.stage-name-input::before {
		content: '✎';
		position: absolute;
		left: 0.5em;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(127, 127, 175, 0.5);
		font-size: 0.8em;
		pointer-events: none;
	}
</style>
