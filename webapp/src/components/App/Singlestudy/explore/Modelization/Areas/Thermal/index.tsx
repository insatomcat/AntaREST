import { useMemo, useState } from "react";
import { createMRTColumnHelper } from "material-react-table";
import { Box } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  getThermalClusters,
  createThermalCluster,
  deleteThermalClusters,
  THERMAL_GROUPS,
  ThermalGroup,
  duplicateThermalCluster,
  type ThermalClusterWithCapacity,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  addClusterCapacity,
  capacityAggregationFn,
  getClustersWithCapacityTotals,
} from "../common/clustersUtils";
import { TRow } from "../../../../../../common/GroupedDataTable/types";
import BooleanCell from "../../../../../../common/GroupedDataTable/cellRenderers/BooleanCell";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";

const columnHelper = createMRTColumnHelper<ThermalClusterWithCapacity>();

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);

  const { data: clustersWithCapacity = [], isLoading } =
    usePromiseWithSnackbarError<ThermalClusterWithCapacity[]>(
      async () => {
        const clusters = await getThermalClusters(study.id, areaId);
        return clusters?.map(addClusterCapacity);
      },
      {
        resetDataOnReload: true,
        errorMessage: t("studies.error.retrieveData"),
        deps: [study.id, areaId],
      },
    );

  const [totals, setTotals] = useState(
    getClustersWithCapacityTotals(clustersWithCapacity),
  );

  const columns = useMemo(() => {
    const { totalUnitCount, totalEnabledCapacity, totalInstalledCapacity } =
      totals;

    return [
      columnHelper.accessor("enabled", {
        header: "Enabled",
        size: 50,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      columnHelper.accessor("mustRun", {
        header: "Must Run",
        size: 50,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      columnHelper.accessor("unitCount", {
        header: "Unit Count",
        size: 50,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue()}
          </Box>
        ),
        Footer: () => <Box color="warning.main">{totalUnitCount}</Box>,
      }),
      columnHelper.accessor("nominalCapacity", {
        header: "Nominal Capacity (MW)",
        size: 220,
        Cell: ({ cell }) => cell.getValue().toFixed(1),
      }),
      columnHelper.accessor("installedCapacity", {
        header: "Enabled / Installed (MW)",
        size: 220,
        aggregationFn: capacityAggregationFn(),
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue() ?? ""}
          </Box>
        ),
        Cell: ({ row }) => (
          <>
            {Math.floor(row.original.enabledCapacity)} /{" "}
            {Math.floor(row.original.installedCapacity)}
          </>
        ),
        Footer: () => (
          <Box color="warning.main">
            {totalEnabledCapacity} / {totalInstalledCapacity}
          </Box>
        ),
      }),
      columnHelper.accessor("marketBidCost", {
        header: "Market Bid (€/MWh)",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue().toFixed(2)}</>,
      }),
    ];
  }, [totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TRow<ThermalGroup>) => {
    const cluster = await createThermalCluster(study.id, areaId, values);
    return addClusterCapacity(cluster);
  };

  const handleDuplicate = async (
    row: ThermalClusterWithCapacity,
    newName: string,
  ) => {
    const cluster = await duplicateThermalCluster(
      study.id,
      areaId,
      row.id,
      newName,
    );

    return { ...row, ...cluster };
  };

  const handleDelete = (rows: ThermalClusterWithCapacity[]) => {
    const ids = rows.map((row) => row.id);
    return deleteThermalClusters(study.id, areaId, ids);
  };

  const handleNameClick = (row: ThermalClusterWithCapacity) => {
    navigate(`${location.pathname}/${row.id}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      isLoading={isLoading}
      data={clustersWithCapacity}
      columns={columns}
      groups={[...THERMAL_GROUPS]}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
      fillPendingRow={(row) => ({
        unitCount: 0,
        enabledCapacity: 0,
        installedCapacity: 0,
        ...row,
      })}
      onDataChange={(data) => {
        setTotals(getClustersWithCapacityTotals(data));
      }}
    />
  );
}

export default Thermal;
