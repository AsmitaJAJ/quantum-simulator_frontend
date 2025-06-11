import React from 'react';
import styled from 'styled-components';

const ReadMore = () => {
  return (
    <StyledWrapper>
      <button id="bottone1"><strong>Read More</strong></button>
    </StyledWrapper>
  );
}

const StyledWrapper = styled.div`
  #bottone1 {
   padding-left: 33px;
   padding-right: 33px;
   padding-bottom: 16px;
   padding-top: 16px;
   border-radius: 9px;
   background:#2596be;
   border: none;
   font-family: inherit;
   text-align: center;
   cursor: pointer;
   transition: 0.4s;
  }

  #bottone1:hover {
   box-shadow: 7px 5px 56px -14px rgb(37, 150, 190);
  }

  #bottone1:active {
   transform: scale(0.97);
   box-shadow: 7px 5px 56px -10px #C3D900;
  }`;

export default ReadMore;
