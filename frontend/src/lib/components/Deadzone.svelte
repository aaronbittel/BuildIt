<script lang="ts">
	import { deleteTaskRequest } from '$lib/api';
	import { fade } from 'svelte/transition';
	import { getStagesState } from '$lib/stages.svelte';

	let isDragover = $state(false);

	const stagesState = getStagesState();

	function ondragover(event: DragEvent) {
		event.preventDefault();
	}

	async function ondrop(event: DragEvent) {
		isDragover = false;
		const raw = event.dataTransfer?.getData('application/json');

		if (!raw) {
			console.error('dragged item had no data attached');
			return;
		}
		const data = JSON.parse(raw);

		if (data.type == 'task') {
			const { task } = data;
			const ok = await deleteTaskRequest(task.id);
			if (ok) {
				// FIXME: handle error case
				stagesState.removeTask(task.stage_id, task.id);
			}
		} else if (data.type == 'stage') {
			const { stageID } = data;
		} else {
			console.error('unknown drag type', data);
		}
	}

	function ondragenter(event: DragEvent) {
		event.preventDefault();
		isDragover = true;
	}

	function ondragleave() {
		isDragover = false;
	}
</script>

<div
	role="region"
	class="delete-zone {isDragover ? 'active' : ''}"
	in:fade
	out:fade
	{ondragover}
	{ondrop}
	{ondragenter}
	{ondragleave}
>
	Drop here to delete
</div>

<style>
	.delete-zone {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 8em;
		margin: 2em auto;
		border: 3px dashed #ff4b5c;
		border-radius: 16px;
		background: linear-gradient(135deg, rgba(255, 75, 92, 0.1), rgba(255, 75, 92, 0.15));
		color: #ff4b5c;
		font-weight: 700;
		font-size: 1.2rem;
		text-align: center;
		transition:
			background 0.2s ease,
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}

	.delete-zone:hover {
		background: linear-gradient(135deg, rgba(255, 75, 92, 0.15), rgba(255, 75, 92, 0.25));
		transform: scale(1.02);
		cursor: pointer;
	}

	.delete-zone.active {
		background: linear-gradient(135deg, rgba(255, 75, 92, 0.2), rgba(255, 75, 92, 0.3));
		box-shadow: 0 0 10px rgba(255, 75, 92, 0.3);
		transform: scale(1.03);
	}
</style>
