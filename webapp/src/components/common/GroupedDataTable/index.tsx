import Box from "@mui/material/Box";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import {
  MaterialReactTable,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  useMaterialReactTable,
  type MRT_RowSelectionState,
  type MRT_ColumnDef,
  type MRT_Row,
} from "material-react-table";
import { useTranslation } from "react-i18next";
import { useMemo, useState } from "react";
import CreateDialog from "./CreateDialog";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import { TRow, generateUniqueValue, getTableOptionsForAlign } from "./utils";
import DuplicateDialog from "./DuplicateDialog";
import { translateWithColon } from "../../../utils/i18nUtils";
import useAutoUpdateRef from "../../../hooks/useAutoUpdateRef";
import * as R from "ramda";
import { usePrevious } from "react-use";
import useUpdateEffectOnce from "../../../hooks/useUpdateEffectOnce";

export interface GroupedDataTableProps<TData extends TRow> {
  data: TData[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: Array<MRT_ColumnDef<TData, any>>;
  groups: string[] | readonly string[];
  onCreate?: (values: TData) => Promise<TData>;
  onDelete?: (ids: string[]) => void;
  onNameClick?: (row: MRT_Row<TData>) => void;
  isLoading?: boolean;
}

// Use ids to identify default columns (instead of `accessorKey`),
// to have a unique identifier. It is more likely to have a duplicate
// `accessorKey` with `columns` prop.
const GROUP_COLUMN_ID = "_group";
const NAME_COLUMN_ID = "_name";

function GroupedDataTable<TData extends TRow>({
  data,
  columns,
  groups,
  onCreate,
  onDelete,
  onNameClick,
  isLoading,
}: GroupedDataTableProps<TData>) {
  const { t } = useTranslation();
  const [openDialog, setOpenDialog] = useState<
    "add" | "duplicate" | "delete" | ""
  >("");
  const [tableData, setTableData] = useState(data);
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});
  // Allow to use the last version of `onNameClick` in `tableColumns`
  const callbacksRef = useAutoUpdateRef({ onNameClick });
  const prevData = usePrevious(data);

  // Update once `data` only if previous value was empty.
  // It allows to handle loading data.
  useUpdateEffectOnce(() => {
    if (prevData && prevData.length === 0) {
      setTableData(data);
    }
  }, [data.length]);

  const existingNames = useMemo(
    () => tableData.map((row) => row.name.toLowerCase()),
    [tableData],
  );

  const tableColumns = useMemo<Array<MRT_ColumnDef<TData>>>(
    () => [
      {
        accessorKey: "group",
        header: t("global.group"),
        id: GROUP_COLUMN_ID,
        size: 50,
        filterVariant: "autocomplete",
        filterSelectOptions: groups,
        footer: translateWithColon("global.total"),
        ...getTableOptionsForAlign("left"),
      },
      {
        accessorKey: "name",
        header: t("global.name"),
        id: NAME_COLUMN_ID,
        size: 100,
        filterVariant: "autocomplete",
        filterSelectOptions: existingNames,
        Cell:
          callbacksRef.current.onNameClick &&
          (({ renderedCellValue, row }) => (
            <Box
              sx={{
                display: "inline",
                "&:hover": {
                  color: "primary.main",
                  textDecoration: "underline",
                },
              }}
              onClick={() => callbacksRef.current.onNameClick?.(row)}
            >
              {renderedCellValue}
            </Box>
          )),
        ...getTableOptionsForAlign("left"),
      },
      ...columns,
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns, t, ...groups],
  );

  const table = useMaterialReactTable({
    data: tableData,
    columns: tableColumns,
    initialState: {
      grouping: [GROUP_COLUMN_ID],
      density: "compact",
      expanded: true,
      columnPinning: { left: [GROUP_COLUMN_ID] },
    },
    state: { isLoading, rowSelection },
    enableGrouping: true,
    enableStickyFooter: true,
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    // Rows
    muiTableBodyRowProps: ({ row }) => ({
      onClick: () => {
        const isGrouped = row.getIsGrouped();
        const rowIds = isGrouped
          ? row.getLeafRows().map((r) => r.id)
          : [row.id];

          setRowSelection((prev) => {
            const newValue = isGrouped
              ? !rowIds.some((id) => prev[id]) // Select/Deselect all
              : !prev[row.id];

          return {
            ...prev,
            ...rowIds.reduce((acc, id) => ({ ...acc, [id]: newValue }), {}),
          };
        });
      },
      selected: rowSelection[row.id],
      sx: { cursor: "pointer" },
    }),
    // Toolbars
    renderTopToolbarCustomActions: ({ table }) => (
      <Box sx={{ display: "flex", gap: 1 }}>
        {onCreate && (
          <Button
            startIcon={<AddCircleOutlineIcon />}
            variant="contained"
            size="small"
            onClick={() => setOpenDialog("add")}
          >
            {t("button.add")}
          </Button>
        )}
        {onCreate && (
          <Button
            startIcon={<ContentCopyIcon />}
            variant="outlined"
            size="small"
            onClick={() => setOpenDialog("duplicate")}
            disabled={table.getSelectedRowModel().rows.length !== 1}
          >
            {t("global.duplicate")}
          </Button>
        )}
        {onDelete && (
          <Button
            startIcon={<DeleteOutlineIcon />}
            color="error"
            variant="outlined"
            size="small"
            onClick={() => setOpenDialog("delete")}
            disabled={table.getSelectedRowModel().rows.length === 0}
          >
            {t("global.delete")}
          </Button>
        )}
      </Box>
    ),
    renderToolbarInternalActions: ({ table }) => (
      <>
        <MRT_ToggleGlobalFilterButton table={table} />
        <MRT_ToggleFiltersButton table={table} />
      </>
    ),
    onRowSelectionChange: setRowSelection,
    // Styles
    ...R.mergeDeepRight(getTableOptionsForAlign("right"), {
      muiTableBodyCellProps: {
        sx: { borderBottom: "1px solid rgba(224, 224, 224, 0.3)" },
      },
    }),
  });

  const selectedRows = table
    .getSelectedRowModel()
    .rows.map((row) => row.original);
  const selectedRow = selectedRows.length === 1 ? selectedRows[0] : null;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TData) => {
    if (onCreate) {
      const newRow = await onCreate(values);
      setTableData((prevTableData) => [...prevTableData, newRow]);
    }
  };

  const handleDelete = () => {
    if (!onDelete) {
      return;
    }

    const rowIndexes = Object.keys(rowSelection)
      .map(Number)
      // ignore groups names
      .filter(Number.isInteger);

    const rowIdsToDelete = rowIndexes.map((index) => tableData[index].id);

    onDelete(rowIdsToDelete);
    setTableData((prevTableData) =>
      prevTableData.filter((row) => !rowIdsToDelete.includes(row.id)),
    );
    setRowSelection({});
    closeDialog();
  };

  const handleDuplicate = async (name: string) => {
    if (!selectedRow) {
      return;
    }

    const id = generateUniqueValue("id", name, tableData);

    const duplicatedRow = {
      ...selectedRow,
      id,
      name,
    };

    if (onCreate) {
      const newRow = await onCreate(duplicatedRow);
      setTableData((prevTableData) => [...prevTableData, newRow]);
      setRowSelection({});
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <MaterialReactTable table={table} />
      {openDialog === "add" && (
        <CreateDialog
          open
          onClose={closeDialog}
          groups={groups}
          existingNames={existingNames}
          onSubmit={handleCreate}
        />
      )}
      {openDialog === "duplicate" && selectedRow && (
        <DuplicateDialog
          open
          onClose={closeDialog}
          onSubmit={handleDuplicate}
          existingNames={existingNames}
          defaultName={generateUniqueValue("name", selectedRow.name, tableData)}
        />
      )}
      {openDialog === "delete" && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          title={t("dialog.title.confirmation")}
          onCancel={closeDialog}
          onConfirm={handleDelete}
          alert="warning"
        >
          {t("studies.modelization.clusters.question.delete")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default GroupedDataTable;
