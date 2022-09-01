import { Box, Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import Form from "../../../../../../common/Form";
import BindingConstForm from "./BindingConstForm";
import { getDefaultValues, BindingConstFields } from "./utils";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import { getClustersAndLinks } from "../../../../../../../services/api/studydata";

interface Props {
  bindingConst: string;
}

function BindingConstView(props: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { bindingConst } = props;
  const res = usePromise(
    () => getDefaultValues(study.id, bindingConst),
    [study.id, bindingConst]
  );
  const optionsRes = usePromise(
    () => getClustersAndLinks(study.id),
    [study.id]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
        <UsePromiseCond
          response={res}
          ifPending={() => <SimpleLoader />}
          ifResolved={(data) => (
            <UsePromiseCond
              response={optionsRes}
              ifPending={() => <SimpleLoader />}
              ifResolved={(options) => (
                <Form
                  autoSubmit
                  config={{ defaultValues: data as BindingConstFields }}
                >
                  {bindingConst && options && (
                    <BindingConstForm
                      study={study}
                      bindingConst={bindingConst}
                      options={options}
                    />
                  )}
                </Form>
              )}
            />
          )}
        />
      </Paper>
    </Box>
  );
}

export default BindingConstView;