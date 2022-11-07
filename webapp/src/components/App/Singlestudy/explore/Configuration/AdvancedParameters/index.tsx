import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { updateStudyData } from "../../../../../../redux/ducks/studyDataSynthesis";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import Form, { SubmitHandlerPlus } from "../../../../../common/Form";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import Fields from "./Fields";
import {
  AdvancedParamsFormFields,
  getAdvancedParamsFormFields,
  setAdvancedParamsFormFields,
} from "./utils";

function AdvancedParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  const res = usePromiseWithSnackbarError(
    () => getAdvancedParamsFormFields(study.id),
    { errorMessage: "Cannot get advanced parameters fields", deps: [study.id] }
  );

  const handleSubmit = async (
    data: SubmitHandlerPlus<AdvancedParamsFormFields>
  ) => {
    const values = { ...data.dirtyValues };

    // Get a comma separated string from accuracyOnCorrelation array as expected by the api
    if (values.accuracyOnCorrelation) {
      values.accuracyOnCorrelation = (
        values.accuracyOnCorrelation as unknown as string[]
      ).join(", ");
    }

    return setAdvancedParamsFormFields(study.id, values).then(() => {
      if (values.renewableGenerationModelling) {
        dispatch(
          updateStudyData({
            id: study.id,
            changes: { enr_modelling: values.renewableGenerationModelling },
          })
        );
      }
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(defaultValues) => (
        <Form config={{ defaultValues }} onSubmit={handleSubmit} autoSubmit>
          <Fields version={Number(study.version)} />
        </Form>
      )}
    />
  );
}

export default AdvancedParameters;
