import { Box, BoxProps, Divider, Typography } from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "../../utils/muiUtils";

interface FieldsetProps extends Omit<BoxProps, "component"> {
  legend?: string | React.ReactNode;
  children: React.ReactNode;
  contentProps?: BoxProps;
}

function Fieldset(props: FieldsetProps) {
  const { legend, children, sx, contentProps, ...rest } = props;

  return (
    <Box
      {...rest}
      component="fieldset"
      sx={mergeSxProp({ border: "none", m: 0 }, sx)}
    >
      {legend && (
        <>
          {RA.isString(legend) ? (
            <Typography
              variant="h5"
              sx={{ fontSize: "1.25rem", fontWeight: 400, lineHeight: 1.334 }}
            >
              {legend}
            </Typography>
          ) : (
            legend
          )}
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Box {...contentProps} sx={mergeSxProp({ pt: 2 }, contentProps?.sx)}>
        {children}
      </Box>
    </Box>
  );
}

export default Fieldset;
