import { ReactNode } from "react";
import { Divider, Box } from "@mui/material";

interface Props {
  left: ReactNode;
  right: ReactNode;
}

function SplitLayoutView(props: Props) {
  const { left, right } = props;

  return (
    <Box
      width="100%"
      display="flex"
      justifyContent="space-evenly"
      alignItems="center"
      overflow="hidden"
      flexGrow="1"
    >
      <Box
        width="20%"
        height="100%"
        position="relative"
        sx={{
          px: 2,
        }}
      >
        {left}
      </Box>
      <Divider
        sx={{ width: "1px", height: "96%" }}
        orientation="vertical"
        variant="middle"
      />
      <Box
        width="calc(80% - 1px)"
        height="96%"
        display="flex"
        justifyContent="center"
        alignItems="flex-start"
        position="relative"
        overflow="hidden"
        sx={{
          px: 2,
        }}
      >
        {right}
      </Box>
    </Box>
  );
}

export default SplitLayoutView;