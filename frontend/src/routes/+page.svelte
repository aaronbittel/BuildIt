<script lang="ts">
	import type { StageResponse, TaskResponse } from '$lib/types';
	import type { PageProps } from './$types';

	import Stage from '$lib/components/Stage.svelte';
	import Deadzone from '$lib/components/Deadzone.svelte';
	import AdminPanel from '$lib/components/AdminPanel.svelte';

	import { updateTaskMoveRequest, resetDBRequest } from '$lib/api';
	import { isDragging } from '$lib/store';
	import { getStatusbarState } from '$lib/status-bar.svelte';
	import { computeCornerLabels } from '$lib/utils';
	import { setStagesState, getStagesState } from '$lib/stages.svelte';

	let { data }: PageProps = $props();
	setStagesState(data.stages);
	const stagesState = getStagesState();

	let showAdmin = $state(false);

	let cornorLabels: string[] = $derived.by(() => {
		const names = data.stages.map((stage) => stage.name);
		return computeCornerLabels(names);
	});

	const statusbarState = getStatusbarState();

	async function onDrop(draggedTask: TaskResponse, targetStageID: number, toIndex: number) {
		const sourceID = draggedTask.stage_id;
		const sourceStage = data.stages.find((stage) => stage.id === sourceID);
		const targetStage = data.stages.find((stage) => stage.id === targetStageID);

		if (!sourceStage || !targetStage)
			throw new Error(
				`somehow there are at least one stage id that was not found: sourceStage=${JSON.stringify(sourceStage)}, targetStage=${JSON.stringify(targetStage)}`
			);

		const fromIndex = sourceStage.tasks.findIndex((t) => t.id === draggedTask.id);

		// no actual update happend
		if (sourceStage.id === targetStage.id && fromIndex === toIndex) return;

		try {
			const updatedStages = await updateTaskMoveRequest(draggedTask.id, targetStage.id, toIndex);
			stagesState.sync(updatedStages);
		} catch (err) {
			console.error(err);
			return;
		}
	}

	function updateTaskName(stage: StageResponse, idx: number, newName: string) {
		stage.tasks[idx].name = newName;
	}

	async function onkeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key == 'r') {
			event.preventDefault();
			data.stages = await resetDBRequest();
			if (data.stages !== undefined) {
				statusbarState.show("Loaded db snapshot 'Current'");
			}
		}
	}

	function handleAddStage() {
		stagesState.addTempStage();
	}
</script>

<svelte:window {onkeydown} />

<header>
	<button class="admin-panel-btn" onclick={() => (showAdmin = !showAdmin)}> ⚙ Admin </button>
	<h1>My Board</h1>
	<button onclick={handleAddStage} class="add-stage-btn">+ Add Stage</button>
</header>
<main>
	<div class="board-wrapper">
		<div class="board">
			{#each stagesState.stages as stage, idx}
				<Stage {stage} {onDrop} {updateTaskName} cornerLabel={cornorLabels[idx]} />
			{/each}
		</div>
	</div>
</main>

{#if showAdmin}
	<AdminPanel currentSnapshot={data.currentSnapshot} allSnapshots={data.allSnapshots} />
{/if}

{#if $isDragging}
	<Deadzone />
{/if}

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
		margin: 2vh 5vh;
	}

	main {
		display: grid;
		grid-template-columns: clamp(1em, 3vw, 10em) 1fr clamp(1em, 3vw, 10em);
		grid-template-areas: '. board .';
	}

	.board-wrapper {
		display: flex;
		justify-content: center;
		overflow-x: auto;
		padding-bottom: 3em;
		grid-area: board;
	}

	.board {
		justify-content: start;
		display: grid;
		grid-auto-flow: column;
		grid-auto-columns: clamp(17em, 18vw, 25em);
		gap: clamp(1em, 2vw, 1.2em);
		overflow: scroll;
		padding-bottom: 3em;
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
	}

	.add-stage-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 16px rgba(80, 70, 255, 0.5);
	}

	.add-stage-btn:active {
		transform: translateY(0);
		box-shadow: 0 3px 8px rgba(80, 70, 255, 0.4);
	}

	.admin-panel-btn {
		background: linear-gradient(135deg, #6d5dfc, #9b86f8);
		color: #fff;
		font-size: 1rem;
		padding: 0.6em 1.4em;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		box-shadow: 0 4px 12px rgba(155, 134, 248, 0.3);
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}

	.admin-panel-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 16px rgba(155, 134, 248, 0.5);
	}

	.admin-panel-btn:active {
		transform: translateY(0);
		box-shadow: 0 3px 8px rgba(155, 134, 248, 0.4);
	}
</style>
