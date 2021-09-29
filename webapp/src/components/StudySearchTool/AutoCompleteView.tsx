/* eslint-disable react-hooks/exhaustive-deps */
import React from 'react';
import { makeStyles, createStyles, Theme, TextField } from '@material-ui/core';
import Autocomplete from '@material-ui/lab/Autocomplete';
import { GenericInfo } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    minWidth: '200px',
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
  },
}));

interface PropTypes {
    label: string;
    list: Array<GenericInfo>;
    value: GenericInfo | undefined;
    setValue: (value: GenericInfo | undefined) => void;
}

const AutoCompleteView = (props: PropTypes) => {
  const { list, label, value, setValue } = props;
  const classes = useStyles();

  return (
    <Autocomplete
      options={list}
      getOptionLabel={(option) => option.name}
      className={classes.root}
      value={value || null}
      onChange={(event: any, newValue: GenericInfo | null) => setValue(newValue !== null ? newValue : undefined)}
      renderInput={(params) => (
        <TextField
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...params}
          className={classes.root}
          size="small"
          label={label}
          variant="outlined"
        />
      )}
    />
  );
};

export default AutoCompleteView;