<script lang="ts">
	import type { PageProps } from './$types';
	import type { StageResponse, TaskResponse } from '$lib/types';
	import { updateTaskRequest, addTaskRequest, resetDB } from '$lib/api';
	import Column from '$lib/components/Column.svelte';

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

		let updatedTask: TaskResponse | undefined;
		try {
			updatedTask = await updateTaskRequest(draggedTask.id, toIndex, {
				stage_id: targetStage.id
			});
		} catch (err) {
			console.error(err);
			return;
		}

		if (sourceStage.id === targetStage.id) {
			if (fromIndex !== toIndex) {
				reorderTasks(sourceStage, fromIndex, toIndex);
			}
			return;
		}

		sourceStage.tasks = sourceStage.tasks.filter(
			(task: TaskResponse) => task.id !== draggedTask.id
		);
		targetStage.tasks.push(updatedTask);
		reorderTasks(targetStage, fromIndex, toIndex);
	}

	async function addItem(stageID: number, taskName: string) {
		const stage = stages.find((s) => s.id === stageID);
		if (!stage) return;

		const newTask = await addTaskRequest(stageID, taskName);
		if (!newTask) return;

		stage.tasks.push(newTask);
	}

	async function onkeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key == 'r') {
			event.preventDefault();
			stages = await resetDB();
		}
	}

	function reorderTasks(source: StageResponse, fromIndex: number, toIndex: number) {
		const [task] = source.tasks.splice(fromIndex, 1);
		source.tasks.splice(toIndex, 0, task);
	}
</script>

<svelte:window {onkeydown} />

<header>
	<h1>My Board</h1>
</header>

<main>
	<div class="board">
		{#each stages as stage}
			<Column {stage} {onDrop} onAddItem={(taskName: string) => addItem(stage.id, taskName)} />
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
