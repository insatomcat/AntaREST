import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";
import type { PartialExceptFor } from "../../../../../../../utils/tsUtils";
import type { ClusterWithCapacity } from "../common/clustersUtils";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const THERMAL_GROUPS = [
  "Gas",
  "Hard Coal",
  "Lignite",
  "Mixed fuel",
  "Nuclear",
  "Oil",
  "Other 1",
  "Other 2",
  "Other 3",
  "Other 4",
] as const;

export const THERMAL_POLLUTANTS = [
  // For study versions >= 860
  "co2",
  "so2",
  "nh3",
  "nox",
  "nmvoc",
  "pm25",
  "pm5",
  "pm10",
  "op1",
  "op2",
  "op3",
  "op4",
  "op5",
] as const;

export const TS_GENERATION_OPTIONS = [
  "use global",
  "force no generation",
  "force generation",
] as const;

export const TS_LAW_OPTIONS = ["geometric", "uniform"] as const;

export const COST_GENERATION_OPTIONS = [
  "SetManually",
  "useCostTimeseries",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ThermalGroup = (typeof THERMAL_GROUPS)[number];

type LocalTSGenerationBehavior = (typeof TS_GENERATION_OPTIONS)[number];
type TimeSeriesLawOption = (typeof TS_LAW_OPTIONS)[number];
type CostGeneration = (typeof COST_GENERATION_OPTIONS)[number];
type ThermalPollutants = {
  [K in (typeof THERMAL_POLLUTANTS)[number]]: number;
};

export interface ThermalCluster extends ThermalPollutants {
  id: string;
  name: string;
  group: ThermalGroup;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
  mustRun: boolean;
  minStablePower: number;
  spinning: number;
  minUpTime: number;
  minDownTime: number;
  marginalCost: number;
  fixedCost: number;
  startupCost: number;
  marketBidCost: number;
  spreadCost: number;
  genTs: LocalTSGenerationBehavior;
  volatilityForced: number;
  volatilityPlanned: number;
  lawForced: TimeSeriesLawOption;
  lawPlanned: TimeSeriesLawOption;
  costGeneration: CostGeneration;
  efficiency: number;
  variableOMCost: number;
}

export type ThermalClusterWithCapacity = ClusterWithCapacity<ThermalCluster>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getClustersUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string => `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`;

const getClusterUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string => `${getClustersUrl(studyId, areaId)}/${clusterId}`;

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
) {
  const res = await client.get<ThermalCluster[]>(
    getClustersUrl(studyId, areaId),
  );
  return res.data;
}

export async function getThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  const res = await client.get<ThermalCluster>(
    getClusterUrl(studyId, areaId, clusterId),
  );
  return res.data;
}

export async function updateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<ThermalCluster>,
) {
  const res = await client.patch<ThermalCluster>(
    getClusterUrl(studyId, areaId, clusterId),
    data,
  );
  return res.data;
}

export async function createThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<ThermalCluster, "name">,
) {
  const res = await client.post<ThermalCluster>(
    getClustersUrl(studyId, areaId),
    data,
  );
  return res.data;
}

export async function duplicateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: ThermalCluster["id"],
  newName: ThermalCluster["name"],
) {
  const res = await client.post<ThermalCluster>(
    `/v1/studies/${studyId}/areas/${areaId}/thermals/${sourceClusterId}`,
    null,
    { params: { newName } },
  );
  return res.data;
}

export async function deleteThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  await client.delete(getClustersUrl(studyId, areaId), { data: clusterIds });
}
