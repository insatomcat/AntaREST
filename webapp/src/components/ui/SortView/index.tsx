import React, { useState } from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles';
import SortButton from './SortButton';
import { SortStatus, SortItem, SortElement } from './utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      marginLeft: theme.spacing(1),
    },
  }));

  interface PropsType {
    itemNames: Array<SortElement>;
    onClick: (item: SortItem) => void;
    defaultValue: SortItem | undefined;
  }

const SortView = (props: PropsType) => {
  const classes = useStyles(props);
  const { itemNames, onClick, defaultValue } = props;
  const [items, setItems] = useState<Array<SortItem>>(itemNames.map((elm) => ({ element: elm, status: defaultValue?.element.id === elm.id ? defaultValue.status : 'NONE' } as SortItem)));

  const onItemClick = (index: number, status: SortStatus) => {
    const tmpItems = items.map((elm, idx) => (idx === index ? elm : ({ element: elm.element, status: 'NONE' } as SortItem)));
    switch (status) {
      case 'INCREASE':
        tmpItems[index].status = 'DECREASE';
        break;
      case 'DECREASE':
        tmpItems[index].status = 'NONE';
        break;

      default:
        tmpItems[index].status = 'INCREASE';
        break;
    }
    setItems(tmpItems);
    onClick(tmpItems[index]);
  };

  return (
    <div className={classes.root}>
      {
            items.map((elm, index) =>
              <SortButton key={elm.element.id} element={elm.element} status={elm.status} onClick={() => onItemClick(index, elm.status)} />)
        }
    </div>
  );
};

export default SortView;
