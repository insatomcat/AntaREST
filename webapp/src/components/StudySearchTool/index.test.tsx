import React from 'react';
import {render, unmountComponentAtNode} from 'react-dom'
import { screen } from '@testing-library/react';
import StudySearchTool from './index'


/** ******************************************* */
/* Test                                         */
/** ******************************************* */

describe('Test StudySearchTool component', (): void => {

    let container : HTMLElement = null;
    beforeEach(() : void =>
    {
        // Sets up a DOM element as a render target
        container = document.createElement("div");

        // We attach the container to 'document'
        document.body.appendChild(container);
    })

    afterEach((): void => {

        // clean
        unmountComponentAtNode(container);
        container.remove();
        container = null;
    })


    it('Test 1', () : void => {
        
    });

})