import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../common/types";
import MatrixInput from "../../../../common/MatrixInput";

function Wind() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/wind/series/wind_${currentArea}`;

  return (
    <MatrixInput study={study} url={url} computStats={MatrixStats.STATS} />
  );
}

export default Wind;