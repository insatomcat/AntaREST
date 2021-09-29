import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '0 0 20%',
    minWidth: '200px',
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
  },
  userInfos: {
    padding: theme.spacing(1),
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    color: theme.palette.primary.main,
  },
  list: {
    padding: theme.spacing(2),
    alignItems: 'center',
  },
  item: {
    backgroundColor: theme.palette.primary.main,
    marginTop: theme.spacing(1),
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
  },
  itemSelected: {
    backgroundColor: theme.palette.secondary.main,
    marginTop: theme.spacing(1),
    '&:hover': {
      backgroundColor: theme.palette.secondary.main,
    },
  },
  itemText: {
    color: 'white',
  },

}));

interface PropTypes {
    items: Array<string>;
    currentItem: string;
    onItemClick: (item: string) => void;
}

const Nav = (props: PropTypes) => {
  const classes = useStyles();
  const { currentItem, items, onItemClick } = props;
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      <List className={classes.list}>
        {
            items.map((item: string) => (
              <ListItem button key={item} onClick={() => onItemClick(item)} className={currentItem === item ? classes.itemSelected : classes.item}>
                <ListItemText primary={t(item)} className={classes.itemText} />
              </ListItem>
            ))
          }
      </List>
    </div>
  );
};

export default Nav;