<script lang="ts">
	import type { SnapshotResponse } from '$lib/types';
	import { enhance } from '$app/forms';
	import { getStatusbarState } from '$lib/status-bar.svelte';

	type Props = {
		currentSnapshot: SnapshotResponse | null;
		allSnapshots: SnapshotResponse[];
	};

	const { currentSnapshot, allSnapshots }: Props = $props();

	let selectedSnapshot = $state(currentSnapshot?.name ?? allSnapshots[0]?.name ?? null);
	const statusBarState = getStatusbarState();
</script>

<section class="panel">
	<header class="panel__header">
		<h2>Database Snapshots</h2>
		<button class="icon-btn" title="Close">✕</button>
	</header>
	<p class={currentSnapshot ? '' : 'text-gray'}>
		Currently active: <strong>{currentSnapshot?.name ?? 'None'}</strong>
	</p>

	<div class="panel__section">
		<h3>Available Snapshots</h3>
		<form
			method="POST"
			action="?/loadSnapshot"
			use:enhance={({ formData }) => {
				const snapshot = formData.get('snapshot') as string;
				return async ({ result, update }) => {
					if (result.type === 'success') {
						statusBarState.show(`Successfully loaded snapshot ${snapshot}`);
					}
					await update();
					selectedSnapshot = snapshot;
				};
			}}
		>
			<div class="snapshot-wrapper">
				<ul class="snapshot-list">
					{#each allSnapshots as snapshot}
						<li>
							<label>
								<input
									type="radio"
									name="snapshot"
									value={snapshot.name}
									bind:group={selectedSnapshot}
								/>
								{snapshot.name}
							</label>
						</li>
					{/each}
				</ul>
			</div>
			<button class="btn primary full">Load Selected</button>
		</form>
	</div>

	<div class="panel__section">
		<h3>Create Snapshot</h3>
		<form
			class="panel__form"
			method="POST"
			action="?/saveSnapshot"
			use:enhance={({ formElement, formData }) => {
				const name = formData.get('name');
				return async ({ result, update }) => {
					if (result.type === 'success') {
						formElement.reset();
						statusBarState.show(`Successfully saved snapshot ${name}`);
					}
					update();
				};
			}}
		>
			<label>
				<span>Name</span>
				<input
					type="text"
					name="name"
					placeholder="Enter file name"
					bind:value={selectedSnapshot}
				/>
			</label>

			<label>
				<span>Comment</span>
				<textarea name="comment" rows="4" placeholder="Describe this snapshot"></textarea>
			</label>

			<button class="btn primary full">Save Snapshot</button>
		</form>
	</div>
</section>

<style>
	.panel {
		position: absolute;
		top: 2rem;
		right: 2rem;
		width: 420px;
		z-index: 100;
		background: rgba(28, 28, 40, 0.99);
		color: #f0f0f0;
		border: 1px solid rgba(93, 63, 211, 0.4);
		border-radius: 18px;
		box-shadow:
			0 8px 28px rgba(0, 0, 0, 0.6),
			0 0 12px rgba(109, 93, 252, 0.3);
		padding: 1.4rem;
		display: grid;
		gap: 1.2rem;
		animation: slideIn 0.3s ease forwards;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(40px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.panel__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-bottom: 0.6rem;
		border-bottom: 1px solid rgba(109, 93, 252, 0.4);
	}

	.panel__header h2 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 600;
		color: #e5e7ff;
	}

	.icon-btn {
		border: none;
		background: transparent;
		color: #bbbafc;
		font-size: 1.3rem;
		cursor: pointer;
		transition:
			color 0.2s ease,
			transform 0.2s ease;
	}
	.icon-btn:hover {
		color: #fff;
		transform: scale(1.1);
	}

	.panel__section {
		display: grid;
		gap: 0.9rem;
		border-top: 1px solid rgba(109, 93, 252, 0.2);
		padding-top: 1rem;
	}

	.panel__section h3 {
		font-size: 1rem;
		font-weight: 500;
		color: #a7a8ff;
	}

	.snapshot-list {
		list-style: none;
		padding: 0;
		margin: 0 0 0.75rem;
		display: grid;
		gap: 0.6rem;

		max-height: 200px;
		overflow-y: auto;
	}

	.snapshot-list li label {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		background: rgba(45, 45, 65, 0.9);
		padding: 0.6rem 0.8rem;
		border-radius: 12px;
		border: 1px solid rgba(109, 93, 252, 0.2);
		font-size: 0.9rem;
		transition:
			background 0.2s ease,
			border 0.2s ease;
		cursor: pointer;
	}

	.snapshot-list li label:hover {
		background: rgba(68, 60, 112, 0.9);
		border-color: rgba(109, 93, 252, 0.4);
	}

	.panel__form {
		display: grid;
		gap: 0.9rem;
	}

	.panel__form label {
		display: grid;
		gap: 0.35rem;
		font-size: 0.85rem;
	}
	.panel__form label span {
		color: #c0c1ff;
	}

	.panel__form input,
	.panel__form textarea {
		width: 100%;
		padding: 0.6rem 0.8rem;
		background: rgba(26, 26, 36, 0.95);
		color: #f3f3ff;
		border: 1px solid rgba(109, 93, 252, 0.3);
		border-radius: 10px;
		font: inherit;
		transition:
			border 0.2s ease,
			box-shadow 0.2s ease;
	}

	.panel__form input:focus,
	.panel__form textarea:focus {
		border-color: #6d5dfc;
		box-shadow: 0 0 6px rgba(109, 93, 252, 0.5);
		outline: none;
	}

	.btn {
		border: none;
		border-radius: 12px;
		padding: 0.7rem 1rem;
		background: rgba(52, 52, 80, 0.9);
		color: #f0f0f0;
		cursor: pointer;
		font-weight: 600;
		font-size: 0.95rem;
		letter-spacing: 0.3px;
		transition:
			background 0.2s ease,
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}
	.btn:hover {
		background: rgba(80, 70, 140, 0.95);
		transform: translateY(-2px);
		box-shadow: 0 4px 10px rgba(109, 93, 252, 0.3);
	}

	.btn.primary {
		background: linear-gradient(135deg, #4a3fdb, #6d5dfc);
		box-shadow: 0 4px 12px rgba(109, 93, 252, 0.4);
	}
	.btn.primary:hover {
		background: linear-gradient(135deg, #5b4feb, #7d6dfd);
	}

	.full {
		width: 100%;
		text-align: center;
	}

	@media (max-width: 480px) {
		.panel {
			width: calc(100% - 2rem);
			right: 1rem;
		}
	}

	.text-gray {
		color: #888;
		font-weight: normal;
	}
</style>
