import {
  Box,
  Button,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  ToggleButtonGroupProps,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext, useParams } from "react-router";
import axios from "axios";
import GridOffIcon from "@mui/icons-material/GridOff";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import {
  Area,
  LinkElement,
  MatrixType,
  StudyMetadata,
} from "../../../../../../common/types";
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getLinks,
  getStudyOutput,
} from "../../../../../../redux/selectors";
import { getStudyData } from "../../../../../../services/api/study";
import { isSearchMatching } from "../../../../../../utils/textUtils";
import EditableMatrix from "../../../../../common/EditableMatrix";
import PropertiesView from "../../../../../common/PropertiesView";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import ListElement from "../../common/ListElement";
import SelectionDrawer, { SelectionDrawerProps } from "./SelectionDrawer";
import { createPath, DataType, OutputItemType, Timestep } from "./utils";
import UsePromiseCond, {
  mergeResponses,
} from "../../../../../common/utils/UsePromiseCond";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { downloadMatrix } from "../../../../../../utils/matrixUtils";

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { outputId } = useParams();

  const outputRes = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudyOutput(state, id, outputId as string),
  });

  const { data: output } = outputRes;
  const [dataType, setDataType] = useState(DataType.General);
  const [timestep, setTimeStep] = useState(Timestep.Hourly);
  const [year, setYear] = useState(-1);
  const [showFilter, setShowFilter] = useState(false);
  const [itemType, setItemType] = useState(OutputItemType.Areas);
  const [selectedItemId, setSelectedItemId] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const { t } = useTranslation();

  const items = useAppSelector((state) =>
    itemType === OutputItemType.Areas
      ? getAreas(state, study.id)
      : getLinks(state, study.id)
  ) as Array<{ id: string; name: string; label?: string }>;

  const filteredItems = useMemo(() => {
    return items.filter((item) =>
      isSearchMatching(searchValue, item.label || item.name)
    );
  }, [items, searchValue]);

  const selectedItem = filteredItems.find(
    (item) => item.id === selectedItemId
  ) as (Area & { id: string }) | LinkElement | undefined;

  useEffect(
    () => {
      const isValidSelectedItem =
        !!selectedItemId &&
        filteredItems.find((item) => item.id === selectedItemId);

      if (!isValidSelectedItem) {
        setSelectedItemId(filteredItems.length > 0 ? filteredItems[0].id : "");
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filteredItems]
  );

  const matrixRes = usePromise<MatrixType | null>(
    async () => {
      if (output && selectedItem) {
        const path = createPath({
          output: { ...output, id: outputId as string },
          item: selectedItem,
          dataType,
          timestep,
          year,
        });

        const res = await getStudyData(study.id, path);
        if (typeof res === "string") {
          const fixed = res
            .replace(/NaN/g, '"NaN"')
            .replace(/Infinity/g, '"Infinity"');

          return JSON.parse(fixed);
        }
        return res;
      }
      return null;
    },
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, output, selectedItem],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleItemTypeChange: ToggleButtonGroupProps["onChange"] = (
    _,
    value: OutputItemType
  ) => {
    setItemType(value);
  };

  const handleSelection: SelectionDrawerProps["onSelection"] = ({
    dataType,
    timestep,
    year,
  }) => {
    setDataType(dataType);
    setTimeStep(timestep);
    setYear(year);
  };

  const handleDownload = (matrixData: MatrixType, fileName: string): void => {
    downloadMatrix(matrixData, fileName);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SplitLayoutView
        left={
          <PropertiesView
            mainContent={
              <>
                <ToggleButtonGroup
                  sx={{ p: 1 }}
                  value={itemType}
                  exclusive
                  size="small"
                  fullWidth
                  onChange={handleItemTypeChange}
                >
                  <ToggleButton value={OutputItemType.Areas}>
                    {t("study.areas")}
                  </ToggleButton>
                  <ToggleButton value={OutputItemType.Links}>
                    {t("study.links")}
                  </ToggleButton>
                </ToggleButtonGroup>
                <ListElement
                  list={filteredItems}
                  currentElement={selectedItemId}
                  currentElementKeyToTest="id"
                  setSelectedItem={(item) => setSelectedItemId(item.id)}
                />
              </>
            }
            onSearchFilterChange={setSearchValue}
          />
        }
        right={
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              height: 1,
              width: 1,
              gap: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                gap: 4,
              }}
            >
              {[
                [
                  `${t("study.results.mc")}:`,
                  year > 0 ? `${t("study.results.mc.year")} ${year}` : "all",
                ],
                [`${t("study.results.display")}:`, dataType],
                [`${t("study.results.temporality")}:`, timestep],
              ].map(([label, value]) => (
                <Box key={label}>
                  <Box component="span" sx={{ opacity: 0.7, mr: 1 }}>
                    {label}
                  </Box>
                  {value}
                </Box>
              ))}
              <Button
                variant="outlined"
                onClick={() => setShowFilter(true)}
                disabled={matrixRes.isLoading}
              >
                {t("global.change")}
              </Button>

              <Button
                variant="outlined"
                color="primary"
                startIcon={<DownloadOutlinedIcon />}
                onClick={() =>
                  matrixRes.data &&
                  handleDownload(matrixRes.data, `matrix_${study.id}`)
                }
                disabled={matrixRes.isLoading}
              >
                {t("global.download")}
              </Button>
            </Box>
            <Box sx={{ flex: 1 }}>
              <UsePromiseCond
                response={mergeResponses(outputRes, matrixRes)}
                ifPending={() => (
                  <Skeleton sx={{ height: 1, transform: "none" }} />
                )}
                ifResolved={([, matrix]) =>
                  matrix && (
                    <EditableMatrix
                      matrix={matrix}
                      matrixTime={false}
                      readOnly
                      toggleView
                    />
                  )
                }
                ifRejected={(err) => (
                  <Box
                    sx={{
                      height: 1,
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      flexDirection: "column",
                      gap: 1,
                    }}
                  >
                    {axios.isAxiosError(err) && err.response?.status === 404 ? (
                      <>
                        <GridOffIcon sx={{ fontSize: "80px" }} />
                        {t("study.results.noData")}
                      </>
                    ) : (
                      t("data.error.matrix")
                    )}
                  </Box>
                )}
              />
            </Box>
          </Box>
        }
      />
      <SelectionDrawer
        open={showFilter}
        onClose={() => setShowFilter(false)}
        values={{ dataType, timestep, year }}
        maxYear={output?.nbyears}
        onSelection={handleSelection}
      />
    </>
  );
}

export default ResultDetails;
