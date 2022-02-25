import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  ListItemText,
  ListItem,
  Typography,
} from '@material-ui/core';
import DeleteIcon from '@material-ui/icons/Delete';
import { useTranslation } from 'react-i18next';
import AutoSizer from 'react-virtualized-auto-sizer';
import { areEqual, FixedSizeList, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from './types';

const ROW_ITEM_SIZE = 40;
const BUTTONS_SIZE = 50;

const hoverStyle = () => ({
  '&:hover': {
    textDecoration: 'underline',
  },
});

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      padding: theme.spacing(1),
      flexGrow: 1,
      flexShrink: 1,
      minHeight: '100px',
      color: theme.palette.primary.main,
    },
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      width: '100%',
      justifyContent: 'flex-end',
      alignItems: 'center',
      display: 'flex',
      height: BUTTONS_SIZE,
    },
    title: {
      width: '90%',
      marginBottom: theme.spacing(0.7),
      color: theme.palette.primary.main,
      boxSizing: 'border-box',
      fontWeight: 'bold',
    },
    list: {
      '&> div > li > div': {
        cursor: 'pointer',
        '&:hover': {
          textDecoration: 'underline',
        },
      },
    },
  }));

interface PropsType {
    links: Array<LinkProperties>;
    node: NodeProperties;
    onDelete: () => void;
    setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { links, node, setSelectedItem } = data;
  const link = links[index].source === node.id ? links[index].target : links[index].source;
  const linkData = links[index].source === node.id ? { source: links[index].source, target: links[index].target } : { source: links[index].target, target: links[index].source };

  return (
    <ListItem key={index} style={style}>
      <ListItemText primary={link} onClick={() => setSelectedItem(linkData)} style={{ width: '100%', ...hoverStyle }} />
    </ListItem>
  );
}, areEqual);

const LinksView = (props: PropsType) => {
  const classes = useStyles();
  const { links, node, onDelete, setSelectedItem } = props;
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      {links.length >= 1 && (
      <Typography className={classes.title}>
        {t('singlestudy:link')}
      </Typography>
      )}
      <AutoSizer>
        {
          ({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * links.length;
            return (
              <>
                <FixedSizeList className={classes.list} height={idealHeight > height - BUTTONS_SIZE ? height - BUTTONS_SIZE : idealHeight} width={width} itemSize={ROW_ITEM_SIZE} itemCount={links.length} itemData={{ links, node, setSelectedItem }}>
                  {Row}
                </FixedSizeList>
                <div className={classes.buttons} style={{ width }}>
                  <DeleteIcon className={classes.deleteIcon} onClick={onDelete} />
                </div>
              </>
            );
          }
        }
      </AutoSizer>
    </div>
  );
};

export default LinksView;