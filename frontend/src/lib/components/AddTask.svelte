<script lang="ts">
	import { tick } from 'svelte';

	let newTaskText: string = $state('');
	let showTaskInput: boolean = $state(false);

	type Props = {
		nameLabel: string;
		onAddItem: (taskName: string) => void;
	};

	const { nameLabel, onAddItem }: Props = $props();

	function handleAddTaskClick() {
		showTaskInput = !showTaskInput;
		if (newTaskText === '') return;

		onAddItem(newTaskText);
		resetTextArea();
	}

	async function handleKeydown(event: KeyboardEvent) {
		if (event.ctrlKey && event.key.toUpperCase() === nameLabel) {
			event.preventDefault();
			showTaskInput = !showTaskInput;

			await tick();
			document.getElementById(`${nameLabel}-textarea`)?.focus();
		}
	}

	function handleEnter(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault(); // prevent newline
			handleAddTaskClick();
			return;
		}
		if (event.key === 'Escape') {
			resetTextArea();
			return;
		}
	}

	function resetTextArea() {
		showTaskInput = false;
		newTaskText = '';
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if showTaskInput}
	<div class="add-task">
		<textarea
			id={`${nameLabel}-textarea`}
			bind:value={newTaskText}
			placeholder="New task"
			onkeydown={(e) => handleEnter(e)}
			onblur={() => handleAddTaskClick()}
		></textarea>
	</div>
{/if}
<button class="btn-add-card" onclick={() => handleAddTaskClick()}>
	<svg viewBox="0 0 24 24">
		<path d="M12 5v14m-7-7h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
	</svg>
	<span>Add another Card</span>
</button>

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

	.add-task textarea {
		font-family: inherit;
		color: inherit;
		line-height: 1.2;
		background: rgba(127, 127, 175, 0.2);
		border: 2px solid #7f7faf;
		border-radius: 0.5em;
		padding: 0.5em;
	}

	.add-task textarea::placeholder {
		color: #dcdcff;
	}
</style>
