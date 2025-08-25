<script lang="ts">
	import { enhance } from '$app/forms';
	import { getStagesState } from '$lib/stages.svelte';
	import type { TaskResponse } from '$lib/types';
	import { tick } from 'svelte';

	let newTaskName: string = $state('');
	let showTaskInput: boolean = $state(false);

	type Props = {
		cornerLabel: string;
		stageID: number;
	};

	const stagesStage = getStagesState();

	const { cornerLabel, stageID }: Props = $props();

	async function handleKeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key.toUpperCase() === cornerLabel) {
			event.preventDefault();
			showTaskInput = !showTaskInput;

			await tick();
			document.getElementById(`${cornerLabel}-textarea`)?.focus();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<form
	method="POST"
	action="?/addTask"
	use:enhance={({ formData }) => {
		const name = formData.get('name') || '';
		if (name === '') {
			showTaskInput = !showTaskInput;
			return;
		}
		formData.append('stageID', String(stageID));
		return async ({ result, update }) => {
			if (result.type === 'success') {
				const task = result.data as TaskResponse;
				stagesStage.addTask(stageID, task);
			}
			showTaskInput = false;
			newTaskName = '';
			update();
		};
	}}
>
	<div class="add-task">
		{#if showTaskInput}
			<textarea
				id={`${cornerLabel}-textarea`}
				name="name"
				bind:value={newTaskName}
				placeholder="New task"
				class="text-input"
			></textarea>
		{/if}
		<button class="btn-add-card" type="submit">
			<svg viewBox="0 0 24 24">
				<path d="M12 5v14m-7-7h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
			</svg>
			<span>Add another Card</span>
		</button>
	</div>
</form>

<style>
	.btn-add-card {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5em;
		background-color: rgba(127, 127, 175, 0.3);
		color: #f0f0f0;
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.5em 0;
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
	}

	.text-input {
		font-family: inherit;
		color: inherit;
		line-height: 1.2;
		background: rgba(127, 127, 175, 0.2);
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.5em;
	}

	.text-input::placeholder {
		color: #dcdcff;
	}
</style>
