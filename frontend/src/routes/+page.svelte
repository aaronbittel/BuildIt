<script lang="ts">
	import type { PageProps } from './$types';
	import type { TaskResponse } from '$lib/types';
	import { updateTaskRequest, addTaskRequest, resetDB } from '$lib/api';
	import Column from '$lib/components/Column.svelte';

	let { data }: PageProps = $props();
	let stages = $state(data.stages);

	async function onDrop(draggedTask: TaskResponse, sourceID: number, targetID: number) {
		if (sourceID === targetID) return;

		const source = stages.find((c) => c.id === sourceID);
		const target = stages.find((c) => c.id === targetID);

		if (!source || !target) return;
		if (source.id === target.id) return;

		try {
			const updatedTask = await updateTaskRequest(draggedTask.id, { stage_id: target.id });
			source.tasks = source.tasks.filter((task: TaskResponse) => task.id !== draggedTask.id);
			target.tasks.push(updatedTask);
		} catch (err) {
			console.error(err);
		}
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
