import type { ColumnType } from "$lib/types";
import type { PageLoad } from "./$types";

export const load: PageLoad = () => {
    const columns: ColumnType[] = [
        {
            key: 'backlog',
            title: 'Backlog',
            items: [
                'add more metadata to the tasks',
                'Order of item depends on drag position',
                'create a backend',
            ],
        },
        {
            key: 'in_progress',
            title: 'In Progress',
            items: [
            ],
        },
        {
            key: 'done',
            title: 'Done',
            items: [],
        }
    ];

    return { columns };
}
