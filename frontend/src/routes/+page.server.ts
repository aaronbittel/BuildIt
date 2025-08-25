import { type Actions, error, fail } from '@sveltejs/kit';

import { BACKEND_PREFIX } from '$lib/api';

export const actions: Actions = {
	loadSnapshot: async ({ request }) => {
		const formdata = await request.formData();
		const name = String(formdata.get('snapshot') ?? '').trim();

		if (!name) {
			return { success: false, reason: 'name field must not be empty' };
		}

		const res = await fetch(`${BACKEND_PREFIX}/dev/snapshots/load`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: name })
		});
		if (!res.ok) {
			return { success: false };
		}

		const responseData = await res.json();
		return { sucess: true, response: responseData };
	},

	saveSnapshot: async ({ request }) => {
		const formdata = await request.formData();
		const name = String(formdata.get('name') ?? '').trim();
		const comment = String(formdata.get('comment') ?? '').trim();

		if (!name) {
			return { success: false, reason: 'name field must not be empty' };
		}

		if (!comment) {
			return { success: false, reason: 'comment field must not be empty' };
		}

		const res = await fetch(`${BACKEND_PREFIX}/dev/snapshots/save`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: name, comment: comment })
		});

		if (!res.ok) {
			return { success: false };
		}

		const responseData = await res.json();
		return { sucess: true, response: responseData };
	},

	addStage: async ({ request }) => {
		const formdata = await request.formData();
		const name = String(formdata.get('name') ?? '').trim();

		if (!name) {
			return { success: false, reason: 'stage name must not be empty' };
		}

		const res = await fetch(`${BACKEND_PREFIX}/stages`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: name })
		});

		if (!res.ok) {
			return { success: false };
		}

		const responseData = await res.json();
		return { success: true, data: responseData };
	},

	addTask: async ({ request }) => {
		const formData = await request.formData();
		const name = String(formData.get('name') ?? '').trim();
		const stageID = String(formData.get('stageID') ?? '').trim();

		if (!name) {
			return fail(400, { error: 'name must not be empty' });
		}

		if (!stageID) {
			throw error(400, "something went wrong, 'stageID' should have been added");
		}

		const res = await fetch(`${BACKEND_PREFIX}/tasks`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: name, stage_id: stageID })
		});

		if (!res.ok) {
			const errorText = await res.text();
			return fail(res.status, { error: `Backend error: ${errorText}` });
		}

		return await res.json();
	}
};
