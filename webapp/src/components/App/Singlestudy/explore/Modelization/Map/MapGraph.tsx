import { AxiosError } from "axios";
import { RefObject, useState } from "react";
import { Graph, GraphLink, GraphNode } from "react-d3-graph";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { LinkProperties, StudyMetadata } from "../../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  StudyMapNode,
  createStudyMapLink,
} from "../../../../../../redux/ducks/studyMaps";
import {
  setCurrentArea,
  setCurrentLink,
} from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { makeLinkId } from "../../../../../../redux/utils";
import Node from "./Node";
import { INITIAL_ZOOM, useRenderNodes } from "./utils";

interface Props {
  height: number;
  width: number;
  links: LinkProperties[];
  nodes: StudyMapNode[];
  graph: RefObject<Graph<StudyMapNode & GraphNode, LinkProperties & GraphLink>>;
  onNodePositionChange: (id: string, x: number, y: number) => void;
}

function MapGraph(props: Props) {
  const { height, width, links, nodes, graph, onNodePositionChange } = props;
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [sourceNode, setSourceNode] = useState("");
  const mapNodes = useRenderNodes(nodes, width, height);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkCreation = (nodeId: string) => {
    if (sourceNode && sourceNode === nodeId) {
      setSourceNode("");
    } else {
      setSourceNode(nodeId);
    }
  };

  const handleOnClickNode = async (nodeId: string) => {
    if (!sourceNode && nodes) {
      dispatch(setCurrentLink(""));
      dispatch(setCurrentArea(nodeId));
    } else if (sourceNode) {
      try {
        await dispatch(
          createStudyMapLink({
            studyId: study.id,
            sourceId: sourceNode,
            targetId: nodeId,
          })
        ).unwrap();
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.createLink"), e as AxiosError);
      } finally {
        setSourceNode("");
      }
    }
  };

  const handleOnClickLink = (source: string, target: string) => {
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(makeLinkId(source, target)));
  };

  const handleGraphClick = () => {
    if (sourceNode) {
      setSourceNode("");
    }
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(""));
  };

  const handleNodePositionChange = (id: string, x: number, y: number) => {
    return onNodePositionChange(
      id,
      x - width / INITIAL_ZOOM / 2 - 0,
      -y + height / 2 + 0
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Graph
      id="graph-id"
      ref={graph}
      data={{
        nodes: mapNodes,
        links: mapNodes.length > 0 ? links : [],
      }}
      config={{
        height,
        width,
        highlightDegree: 0,
        staticGraphWithDragAndDrop: true,
        d3: {
          disableLinkForce: true,
        },
        node: {
          renderLabel: false,
          // eslint-disable-next-line react/no-unstable-nested-components
          viewGenerator: (node) => (
            <Node node={node} linkCreation={handleLinkCreation} />
          ),
        },
        link: {
          color: "#a3a3a3",
          strokeWidth: 2,
        },
      }}
      onClickNode={handleOnClickNode}
      onClickLink={handleOnClickLink}
      onClickGraph={handleGraphClick}
      onNodePositionChange={handleNodePositionChange}
    />
  );
}

export default MapGraph;
