import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../common/page/SimpleContent";
import BindingConstPropsView from "./BindingConstPropsView";
import {
  getBindingConst,
  getCurrentBindingConstId,
} from "../../../../../../redux/selectors";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../redux/ducks/studySyntheses";
import BindingConstView from "./BindingConstView";
import usePromise from "../../../../../../hooks/usePromise";
import { getBindingConstraintList } from "../../../../../../services/api/studydata";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import { useEffect } from "react";
import SplitView from "../../../../../common/SplitView";

function BindingConstraints() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  const currentConstraintId = useAppSelector(getCurrentBindingConstId);

  const bindingConstraints = useAppSelector((state) =>
    getBindingConst(state, study.id),
  );

  // TODO find better name
  const constraints = usePromise(
    () => getBindingConstraintList(study.id),
    [study.id, bindingConstraints],
  );

  useEffect(() => {
    if (constraints.data && !currentConstraintId) {
      const firstConstraintId = constraints.data[0].id;
      dispatch(setCurrentBindingConst(firstConstraintId));
    }
  }, [constraints, currentConstraintId, dispatch]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConstraintChange = (bindingConstId: string): void => {
    dispatch(setCurrentBindingConst(bindingConstId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={constraints}
      ifPending={() => <SimpleLoader />}
      ifResolved={(data) => (
        <SplitView direction="horizontal" sizes={[10, 90]} gutterSize={2}>
          <Box>
            <BindingConstPropsView // TODO rename ConstraintsList
              onClick={handleConstraintChange}
              list={data}
              studyId={study.id}
              currentBindingConst={currentConstraintId}
            />
          </Box>
          <Box>
            {currentConstraintId && (
              <BindingConstView constraintId={currentConstraintId} />
            )}
          </Box>
        </SplitView>
      )}
      ifRejected={(error) => <SimpleContent title={error?.toString()} />}
    />
  );
}

export default BindingConstraints;
