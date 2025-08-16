import type { Column } from "$lib/types/board";
import type { PageLoad } from "./$types";

export const load: PageLoad = () => {
    const columns: Column[] = [
        {
            key: 'backlog',
            title: 'Backlog',
            items: [
                'add button for creating new tasks',
                'add more metadata to the tasks',
                'Order of item depends on drag position',
                'create a backend',
            ],
            isDragover: false
        },
        {
            key: 'in_progress',
            title: 'In Progress',
            items: [],
            isDragover: false
        },
        {
            key: 'done',
            title: 'Done',
            items: [],
            isDragover: false
        }
    ];

    return { columns };
}
