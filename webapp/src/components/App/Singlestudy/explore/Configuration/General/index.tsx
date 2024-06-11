import { useOutletContext } from "react-router";
import * as R from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import ScenarioPlaylistDialog from "./dialogs/ScenarioPlaylistDialog";
import {
  GeneralFormFields,
  getGeneralFormFields,
  hasDayField,
  pickDayFields,
  SetDialogStateType,
  setGeneralFormFields,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import ScenarioBuilderDialog from "./dialogs/ScenarioBuilderDialog";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<SetDialogStateType>("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<GeneralFormFields>) => {
    const { values, dirtyValues } = data;
    const newValues = hasDayField(dirtyValues)
      ? {
          ...dirtyValues,
          // Required by server to validate values
          ...pickDayFields(values),
        }
      : dirtyValues;

    return setGeneralFormFields(study.id, newValues);
  };

  const handleCloseDialog = () => setDialog("");

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Form
        key={study.id}
        config={{ defaultValues: () => getGeneralFormFields(study.id) }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        <Fields setDialog={setDialog} />
      </Form>
      {R.cond([
        [
          R.equals("thematicTrimming"),
          () => (
            <ThematicTrimmingDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
        [
          R.equals("scenarioBuilder"),
          () => (
            <ScenarioBuilderDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
        [
          R.equals("scenarioPlaylist"),
          () => (
            <ScenarioPlaylistDialog
              open
              study={study}
              onClose={handleCloseDialog}
            />
          ),
        ],
      ])(dialog)}
    </>
  );
}

export default GeneralParameters;
