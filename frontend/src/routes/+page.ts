import type { SnapshotResponse, StageResponse } from '$lib/types';

import { BACKEND_PREFIX } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const stagesResponse = await fetch(`${BACKEND_PREFIX}/stages/tasks`);
	if (!stagesResponse.ok) {
		console.error('Failed to fetch stages', stagesResponse.status);
	}
	const stages: StageResponse[] = await stagesResponse.json();

	const snapshotResponse = await fetch(`${BACKEND_PREFIX}/dev/snapshots/current`);
	let currentSnapshot: SnapshotResponse | null = null;
	if (!snapshotResponse.ok) {
		console.error('Failed to fetch current snapshot', snapshotResponse.status);
	} else {
		currentSnapshot = await snapshotResponse.json();
	}

	const allSnapshotsResponse = await fetch(`${BACKEND_PREFIX}/dev/snapshots`);
	if (!allSnapshotsResponse.ok) {
		console.error('Failed to fetch all snapshots', allSnapshotsResponse.status);
	}
	const allSnapshots: SnapshotResponse[] = await allSnapshotsResponse.json();

	return {
		stages,
		currentSnapshot,
		allSnapshots
	};
};
