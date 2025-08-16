import type { Column } from "$lib/types/board";
import type { PageLoad } from "./$types";

export const load: PageLoad = () => {
    const columns: Column[] = [
        {
            key: 'backlog',
            title: 'Backlog',
            items: [
                'extract columns into a Component',
                'add more metadata to the tasks',
                'Order of item depends on drag position',
                'create a backend',
            ],
            isDragover: false,
            showAddButton: true,
        },
        {
            key: 'in_progress',
            title: 'In Progress',
            items: [
                'add button for creating new tasks',
            ],
            isDragover: false,
            showAddButton: true,
        },
        {
            key: 'done',
            title: 'Done',
            items: [],
            isDragover: false,
            showAddButton: true,
        }
    ];

    return { columns };
}
