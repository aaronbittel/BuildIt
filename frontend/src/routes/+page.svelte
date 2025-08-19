<script lang="ts">
	import type { PageProps } from './$types';
	import type { StageResponse, TaskResponse } from '$lib/types';
	import { updateTaskMoveRequest, addTaskRequest, resetDB } from '$lib/api';
	import Stage from '$lib/components/Stage.svelte';

	let { data }: PageProps = $props();
	let stages = $state(data.stages);

	async function onDrop(
		draggedTask: TaskResponse,
		sourceID: number,
		targetID: number,
		toIndex: number
	) {
		const sourceStage = stages.find((c) => c.id === sourceID);
		const targetStage = stages.find((c) => c.id === targetID);

		if (!sourceStage || !targetStage)
			throw new Error('somehow there are at least one stage id was not found');

		const fromIndex = sourceStage.tasks.findIndex((t) => t.id === draggedTask.id);

		// no actual update happend
		if (sourceStage.id === targetStage.id && fromIndex === toIndex) return;

		try {
			const updatedStages = await updateTaskMoveRequest(draggedTask.id, targetStage.id, toIndex);
			stages = updatedStages;
		} catch (err) {
			console.error(err);
			return;
		}
	}

	async function addItem(stageID: number, taskName: string) {
		const stage = stages.find((s) => s.id === stageID);
		if (!stage) return;

		const newTask = await addTaskRequest(stageID, taskName);
		if (!newTask) return;

		stage.tasks.push(newTask);
	}

	function updateTaskName(stage: StageResponse, idx: number, newName: string) {
		stage.tasks[idx].name = newName;
	}

	async function onkeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key == 'r') {
			event.preventDefault();
			stages = await resetDB();
		}
	}
</script>

<svelte:window {onkeydown} />

<header>
	<h1>My Board</h1>
	<button class="add-stage-btn">+ Add Stage</button>
</header>

<main>
	<div class="board">
		{#each stages as stage}
			<Stage
				{stage}
				{onDrop}
				onAddItem={(taskName: string) => addItem(stage.id, taskName)}
				{updateTaskName}
			/>
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
		justify-content: space-between;
		align-items: center;
		height: 100px;
		margin: 0 5%;
	}

	.add-stage-btn {
		background: linear-gradient(135deg, #4a3fdb, #6d5dfc);
		color: #fff;
		font-size: 1.1rem;
		padding: 0.6em 1.4em;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		box-shadow: 0 4px 12px rgba(80, 70, 255, 0.3);
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
		margin-left: 1em;
	}

	.add-stage-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 16px rgba(80, 70, 255, 0.5);
	}

	.add-stage-btn:active {
		transform: translateY(0);
		box-shadow: 0 3px 8px rgba(80, 70, 255, 0.4);
	}

	main {
		display: grid;
		grid-template-columns: 7% 1fr 7%;
		grid-template-areas: '. board .';
	}

	.board {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
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
