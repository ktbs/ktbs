# -*- coding=utf-8 -*-
#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""I provide a REST-Console, bundled in a single HTML file.
"""

REST_CONSOLE = r"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"></meta>
    <base href="" />
    <title>REST-Console</title>
    <style type="text/css">
/* importing gereco.css */
#addressbar {
    width: 100%;
}

.combo {
    overflow-x: visible;
}

.combo *
{
    transition: all .3s;
}

.combo input:disabled
{
    opacity: 0;
    width: 0;
    border: 0;
    padding: 0;
    margin: 0;
}

#method input:enabled,
#method select
{
    width: 6em;
}

#ctype input:enabled,
#ctype select
{
    width: 12em;
}

.subtoolbar {
    display: inline-block;
    margin-left: 2em;
}

#payload {
    transition: all .5s;
    width: 100%;
    height: 20em;
}

#payload:disabled {
    height: 0;
    opacity: 0;
}

#response {
    min-width: fit-content;
    min-width: -moz-fit-content;
    min-width: -webkit-fit-content;
}

#response iframe {
  border: none;
}
    </style>
    <style id="theme" type="text/css">
/* importing theme.css */
#response {
    transition: all .3s;
    border: 1px solid gray;
    background-color: lightYellow;
    padding: .5em;
}

#response.loading {
    border-color: darkGrey;
    background-color: lightGrey;
    color: black;
}

#response.error {
    border: 1px solid red;
    background-color: lightPink;
    color: red;
}

#response a {
    text-decoration: none;
}

#response-headers th {
    text-align: left;
    vertical-align: top;
}

#response-headers ul {
    margin: 0;
    padding: 0;
    list-style: none;
}

#response-headers th, #response-headers td {
  font-family: monospace;
  border-top: thin solid lightGray;
}
    </style>
  </head>
  <body>

    <input id="addressbar" />
    <div class="toolbar">

      <span id="method" class="combo"
        ><input placeholder="GET" disabled="" /
        ><select>
          <option>GET</option>
          <option>PUT</option>
          <option>POST</option>
          <option>DELETE</option>
          <option value="custom">custom</option>
        </select>
      </span>

      <span id="ctype" class="combo"
        ><input placeholder="*/*" disabled="" /
        ><select>
          <option>*/*</option>
          <option>x-gereco/*</option>
          <option>application/json</option>
          <option>application/sparql-query</option>
          <option>application/xml</option>
          <option>text/plain</option>
          <option>text/turtle</option>
          <option value="custom">custom</option>
        </select>
      </span>

      <button id="send">Send</button>

      <div class="subtoolbar" id="hjson-toolbar" style="display: none">
        <button id="tohjson">Json → Hjson</button>
        <button id="fromhjson">Hjson → Json</button>
        <a href="https://hjson.org/"><abbr title="HJson ?">⍰</abbr></a>
      </div>
    </div>

    <textarea id="payload" disabled=""></textarea>

    <pre id="response">
      <span id="loading">loading...</span>
    </pre>

    <table id="response-headers"></table>

    <script type="application/javascript" async
>
/* importing hjson.min.js */
/*!
 * Hjson v3.1.0
 * http://hjson.org
 *
 * Copyright 2014-2017 Christian Zangl, MIT license
 * Details and documentation:
 * https://github.com/hjson/hjson-js
 *
 * This code is based on the the JSON version by Douglas Crockford:
 * https://github.com/douglascrockford/JSON-js (json_parse.js, json2.js)
 */
!function(n){if("object"==typeof exports&&"undefined"!=typeof module)module.exports=n();else if("function"==typeof define&&define.amd)define([],n);else{var e;e="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:this,e.Hjson=n()}}(function(){return function n(e,r,t){function o(a,u){if(!r[a]){if(!e[a]){var s="function"==typeof require&&require;if(!u&&s)return s(a,!0);if(i)return i(a,!0);var f=new Error("Cannot find module '"+a+"'");throw f.code="MODULE_NOT_FOUND",f}var c=r[a]={exports:{}};e[a][0].call(c.exports,function(n){var r=e[a][1][n];return o(r?r:n)},c,c.exports,n,e,r,t)}return r[a].exports}for(var i="function"==typeof require&&require,a=0;a<t.length;a++)o(t[a]);return o}({1:[function(n,e,r){"use strict";function t(n,e,r){var t;return n&&(t={b:n}),e&&((t=t||{}).a=e),r&&((t=t||{}).x=r),t}function o(n,e){if(null!==n&&"object"==typeof n){var r=h.getComment(n);r&&h.removeComment(n);var i,a,s,f;if("[object Array]"===Object.prototype.toString.apply(n)){for(f={a:[]},i=0,a=n.length;i<a;i++)u(f.a,i,r.a[i],o(n[i]))&&(s=!0);!s&&r.e&&(f.e=t(r.e[0],r.e[1]),s=!0)}else{f={s:{}};var c,l=Object.keys(n);for(r&&r.o?(c=[],r.o.concat(l).forEach(function(e){Object.prototype.hasOwnProperty.call(n,e)&&c.indexOf(e)<0&&c.push(e)})):c=l,f.o=c,i=0,a=c.length;i<a;i++){var p=c[i];u(f.s,p,r.c[p],o(n[p]))&&(s=!0)}!s&&r.e&&(f.e=t(r.e[0],r.e[1]),s=!0)}return e&&r&&r.r&&(f.r=t(r.r[0],r.r[1])),s?f:void 0}}function i(){var n="";return[].forEach.call(arguments,function(e){e&&""!==e.trim()&&(n&&(n+="; "),n+=e.trim())}),n}function a(n,e){var r=[];if(c(n,e,r,[]),r.length>0){var t=l(e,null,1);t+="\n# Orphaned comments:\n",r.forEach(function(n){t+=("# "+n.path.join("/")+": "+i(n.b,n.a,n.e)).replace("\n","\\n ")+"\n"}),l(e,t,1)}}function u(n,e,r,o){var i=t(r?r[0]:void 0,r?r[1]:void 0,o);return i&&(n[e]=i),i}function s(n,e){var r=t(e.b,e.a);return r.path=n,r}function f(n,e,r){if(n){var t,o;if(n.a)for(t=0,o=n.a.length;t<o;t++){var i=r.slice().concat([t]),a=n.a[t];a&&(e.push(s(i,a)),f(a.x,e,i))}else n.o&&n.o.forEach(function(t){var o=r.slice().concat([t]),i=n.s[t];i&&(e.push(s(o,i)),f(i.x,e,o))});n.e&&e.push(s(r,n.e))}}function c(n,e,r,t){if(n){if(null===e||"object"!=typeof e)return void f(n,r,t);var o,i,a=h.createComment(e);if(0===t.length&&n.r&&(a.r=[n.r.b,n.r.a]),"[object Array]"===Object.prototype.toString.apply(e)){for(a.a=[],o=0,i=(n.a||[]).length;o<i;o++){var u=t.slice().concat([o]),l=n.a[o];l&&(o<e.length?(a.a.push([l.b,l.a]),c(l.x,e[o],r,u)):(r.push(s(u,l)),f(l.x,r,u)))}0===o&&n.e&&(a.e=[n.e.b,n.e.a])}else a.c={},a.o=[],(n.o||[]).forEach(function(o){var i=t.slice().concat([o]),u=n.s[o];Object.prototype.hasOwnProperty.call(e,o)?(a.o.push(o),u&&(a.c[o]=[u.b,u.a],c(u.x,e[o],r,i))):u&&(r.push(s(i,u)),f(u.x,r,i))}),n.e&&(a.e=[n.e.b,n.e.a])}}function l(n,e,r){var t=h.createComment(n,h.getComment(n));return t.r||(t.r=["",""]),(e||""===e)&&(t.r[r]=h.forceComment(e)),t.r[r]||""}var h=n("./hjson-common");e.exports={extract:function(n){return o(n,!0)},merge:a,header:function(n,e){return l(n,e,0)},footer:function(n,e){return l(n,e,1)}}},{"./hjson-common":2}],2:[function(n,e,r){"use strict";function t(n,e){function r(){return o=n.charAt(s),s++,o}var t,o,i="",a=0,u=!0,s=0;for(r(),"-"===o&&(i="-",r());o>="0"&&o<="9";)u&&("0"==o?a++:u=!1),i+=o,r();if(u&&a--,"."===o)for(i+=".";r()&&o>="0"&&o<="9";)i+=o;if("e"===o||"E"===o)for(i+=o,r(),"-"!==o&&"+"!==o||(i+=o,r());o>="0"&&o<="9";)i+=o,r();for(;o&&o<=" ";)r();return e&&(","!==o&&"}"!==o&&"]"!==o&&"#"!==o&&("/"!==o||"/"!==n[s]&&"*"!==n[s])||(o=0)),t=+i,o||a||!isFinite(t)?void 0:t}function o(n,e){return Object.defineProperty&&Object.defineProperty(n,"__COMMENTS__",{enumerable:!1,writable:!0}),n.__COMMENTS__=e||{}}function i(n){Object.defineProperty(n,"__COMMENTS__",{value:void 0})}function a(n){return n.__COMMENTS__}function u(n){if(!n)return"";var e,r,t,o,i=n.split("\n");for(t=0;t<i.length;t++)for(e=i[t],o=e.length,r=0;r<o;r++){var a=e[r];if("#"===a)break;if("/"===a&&("/"===e[r+1]||"*"===e[r+1])){"*"===e[r+1]&&(t=i.length);break}if(a>" "){i[t]="# "+e;break}}return i.join("\n")}var s=n("os");e.exports={EOL:s.EOL||"\n",tryParseNumber:t,createComment:o,removeComment:i,getComment:a,forceComment:u}},{os:8}],3:[function(n,e,r){"use strict";function t(n,e){function r(n){return"[object Function]"==={}.toString.call(n)}if("[object Array]"!==Object.prototype.toString.apply(n)){if(n)throw new Error("dsf option must contain an array!");return i}if(0===n.length)return i;var t=[];return n.forEach(function(n){if(!n.name||!r(n.parse)||!r(n.stringify))throw new Error("extension does not match the DSF interface");t.push(function(){try{if("parse"==e)return n.parse.apply(null,arguments);if("stringify"==e){var r=n.stringify.apply(null,arguments);if(void 0!==r&&("string"!=typeof r||0===r.length||'"'===r[0]||[].some.call(r,function(n){return a(n)})))throw new Error("value may not be empty, start with a quote or contain a punctuator character except colon: "+r);return r}throw new Error("Invalid type")}catch(e){throw new Error("DSF-"+n.name+" failed; "+e.message)}})}),o.bind(null,t)}function o(n,e){if(n)for(var r=0;r<n.length;r++){var t=n[r](e);if(void 0!==t)return t}}function i(){}function a(n){return"{"===n||"}"===n||"["===n||"]"===n||","===n}function u(){return{name:"math",parse:function(n){switch(n){case"+inf":case"inf":case"+Inf":case"Inf":return 1/0;case"-inf":case"-Inf":return-(1/0);case"nan":case"NaN":return NaN}},stringify:function(n){if("number"==typeof n)return 1/n===-(1/0)?"-0":n===1/0?"Inf":n===-(1/0)?"-Inf":isNaN(n)?"NaN":void 0}}}function s(n){var e=n&&n.out;return{name:"hex",parse:function(n){if(/^0x[0-9A-Fa-f]+$/.test(n))return parseInt(n,16)},stringify:function(n){if(e&&Number.isInteger(n))return"0x"+n.toString(16)}}}function f(){return{name:"date",parse:function(n){if(/^\d{4}-\d{2}-\d{2}$/.test(n)||/^\d{4}-\d{2}-\d{2}T\d{2}\:\d{2}\:\d{2}(?:.\d+)(?:Z|[+-]\d{2}:\d{2})$/.test(n)){var e=Date.parse(n);if(!isNaN(e))return new Date(e)}},stringify:function(n){if("[object Date]"===Object.prototype.toString.call(n)){var e=n.toISOString();return e.indexOf("T00:00:00.000Z",e.length-14)!==-1?e.substr(0,10):e}}}}u.description="support for Inf/inf, -Inf/-inf, Nan/naN and -0",s.description="parse hexadecimal numbers prefixed with 0x",f.description="support ISO dates",e.exports={loadDsf:t,std:{math:u,hex:s,date:f}}},{}],4:[function(n,e,r){"use strict";e.exports=function(e,r){function t(){x=0,O=" "}function o(n){return"{"===n||"}"===n||"["===n||"]"===n||","===n||":"===n}function i(n){var e,r=0,t=1;for(e=x-1;e>0&&"\n"!==w[e];e--,r++);for(;e>0;e--)"\n"===w[e]&&t++;throw new Error(n+" at line "+t+","+r+" >>>"+w.substr(x-r,20)+" ...")}function a(){return O=w.charAt(x),x++,O}function u(n){return w.charAt(x+n)}function s(n){for(var e="",r=O;a();){if(O===r)return a(),n&&"'"===r&&"'"===O&&0===e.length?(a(),f()):e;if("\\"===O)if(a(),"u"===O){for(var t=0,o=0;o<4;o++){a();var u,s=O.charCodeAt(0);O>="0"&&O<="9"?u=s-48:O>="a"&&O<="f"?u=s-97+10:O>="A"&&O<="F"?u=s-65+10:i("Bad \\u char "+O),t=16*t+u}e+=String.fromCharCode(t)}else{if("string"!=typeof S[O])break;e+=S[O]}else"\n"===O||"\r"===O?i("Bad string containing newline"):e+=O}i("Bad string")}function f(){function n(){for(var n=t;O&&O<=" "&&"\n"!==O&&n-- >0;)a()}for(var e="",r=0,t=0;;){var o=u(-t-5);if(!o||"\n"===o)break;t++}for(;O&&O<=" "&&"\n"!==O;)a();for("\n"===O&&(a(),n());;){if(O){if("'"===O){if(r++,a(),3===r)return"\n"===e.slice(-1)&&(e=e.slice(0,-1)),e;continue}for(;r>0;)e+="'",r--}else i("Bad multiline string");"\n"===O?(e+="\n",a(),n()):("\r"!==O&&(e+=O),a())}}function c(){if('"'===O||"'"===O)return s(!1);for(var n="",e=x,r=-1;;){if(":"===O)return n?r>=0&&r!==n.length&&(x=e+r,i("Found whitespace in your key name (use quotes to include)")):i("Found ':' but no key name (for an empty key name use quotes)"),n;O<=" "?O?r<0&&(r=n.length):i("Found EOF while looking for a key name (check your syntax)"):o(O)?i("Found '"+O+"' where a key name was expected (check your syntax or use quotes if the key name includes {}[],: or whitespace)"):n+=O,a()}}function l(){for(;O;){for(;O&&O<=" ";)a();if("#"===O||"/"===O&&"/"===u(0))for(;O&&"\n"!==O;)a();else{if("/"!==O||"*"!==u(0))break;for(a(),a();O&&("*"!==O||"/"!==u(0));)a();O&&(a(),a())}}}function h(){var n=O;for(o(O)&&i("Found a punctuator character '"+O+"' when expecting a quoteless string (check your syntax)");;){a();var e="\r"===O||"\n"===O||""===O;if(e||","===O||"}"===O||"]"===O||"#"===O||"/"===O&&("/"===u(0)||"*"===u(0))){var r=n[0];switch(r){case"f":if("false"===n.trim())return!1;break;case"n":if("null"===n.trim())return null;break;case"t":if("true"===n.trim())return!0;break;default:if("-"===r||r>="0"&&r<="9"){var t=C.tryParseNumber(n);if(void 0!==t)return t}}if(e){n=n.trim();var s=E(n);return void 0!==s?s:n}}n+=O}}function p(n,e){var r;for(n--,r=x-2;r>n&&w[r]<=" "&&"\n"!==w[r];r--);"\n"===w[r]&&r--,"\r"===w[r]&&r--;var t=w.substr(n,r-n+1);for(r=0;r<t.length;r++)if(t[r]>" "){var o=t.indexOf("\n");if(o>=0){var i=[t.substr(0,o),t.substr(o+1)];return e&&0===i[0].trim().length&&i.shift(),i}return[t]}return[]}function m(n){function e(n,r){var t,o,i,a;switch(typeof n){case"string":n.indexOf(r)>=0&&(a=n);break;case"object":if("[object Array]"===Object.prototype.toString.apply(n))for(t=0,i=n.length;t<i;t++)a=e(n[t],r)||a;else for(o in n)Object.prototype.hasOwnProperty.call(n,o)&&(a=e(n[o],r)||a)}return a}function r(r){var t=e(n,r);return t?"found '"+r+"' in a string value, your mistake could be with:\n  > "+t+"\n  (unquoted strings contain everything up to the next line!)":""}return r("}")||r("]")}function d(){var n,e,r,t=[];try{if(k&&(n=C.createComment(t,{a:[]})),a(),e=x,l(),n&&(r=p(e,!0).join("\n")),"]"===O)return a(),n&&(n.e=[r]),t;for(;O;){if(t.push(y()),e=x,l(),","===O&&(a(),e=x,l()),n){var o=p(e);n.a.push([r||"",o[0]||""]),r=o[1]}if("]"===O)return a(),n&&(n.a[n.a.length-1][1]+=r||""),t;l()}i("End of input while parsing an array (missing ']')")}catch(n){throw n.hint=n.hint||m(t),n}}function g(n){var e,r,t,o="",u={};try{if(k&&(e=C.createComment(u,{c:{},o:[]})),n?r=1:(a(),r=x),l(),e&&(t=p(r,!0).join("\n")),"}"===O&&!n)return e&&(e.e=[t]),a(),u;for(;O;){if(o=c(),l(),":"!==O&&i("Expected ':' instead of '"+O+"'"),a(),u[o]=y(),r=x,l(),","===O&&(a(),r=x,l()),e){var s=p(r);e.c[o]=[t||"",s[0]||""],t=s[1],e.o.push(o)}if("}"===O&&!n)return a(),e&&(e.c[o][1]+=t||""),u;l()}if(n)return u;i("End of input while parsing an object (missing '}')")}catch(n){throw n.hint=n.hint||m(u),n}}function y(){switch(l(),O){case"{":return g();case"[":return d();case"'":case'"':return s(!0);default:return h()}}function v(n,e){var r=x;if(l(),O&&i("Syntax error, found trailing characters"),k){var t=e.join("\n"),o=p(r).join("\n");if(o||t){var a=C.createComment(n,C.getComment(n));a.r=[t,o]}}return n}function b(){l();var n=k?p(1):null;switch(O){case"{":return v(g(),n);case"[":return v(d(),n);default:return v(y(),n)}}function j(){l();var n=k?p(1):null;switch(O){case"{":return v(g(),n);case"[":return v(d(),n)}try{return v(g(!0),n)}catch(e){t();try{return v(y(),n)}catch(n){throw e}}}var w,x,O,k,E,C=n("./hjson-common"),q=n("./hjson-dsf"),S={'"':'"',"'":"'","\\":"\\","/":"/",b:"\b",f:"\f",n:"\n",r:"\r",t:"\t"};if("string"!=typeof e)throw new Error("source is not a string");var N=null,_=!0;return r&&"object"==typeof r&&(k=r.keepWsc,N=r.dsf,_=r.legacyRoot!==!1),E=q.loadDsf(N,"parse"),w=e,t(),_?j():b()}},{"./hjson-common":2,"./hjson-dsf":3}],5:[function(n,e,r){"use strict";e.exports=function(e,r){function t(n,e){return P+=n[0].length+n[1].length-n[2]-n[3],n[0]+e+n[1]}function o(n){return n.replace(S,function(n){var e=F[n];return"string"==typeof e?t(x.esc,e):t(x.uni,("0000"+n.charCodeAt(0).toString(16)).slice(-4))})}function i(n,e,r,i){return n?(N.lastIndex=0,I.lastIndex=0,y||r||N.test(n)||void 0!==f.tryParseNumber(n,!0)||I.test(n)?(S.lastIndex=0,_.lastIndex=0,S.test(n)?_.test(n)||i||!b?t(x.qstr,o(n)):a(n,e):t(x.qstr,n)):t(x.str,n)):t(x.qstr,"")}function a(n,e){var r,o=n.replace(/\r/g,"").split("\n");if(e+=p,1===o.length)return t(x.mstr,o[0]);var i=h+e+x.mstr[0];for(r=0;r<o.length;r++)i+=h,o[r]&&(i+=e+o[r]);return i+h+e+x.mstr[1]}function u(n){return n?g||A.test(n)?(S.lastIndex=0,t(x.qkey,S.test(n)?o(n):n)):t(x.key,n):'""'}function s(n,e,r,o){function a(n){return n&&"\n"===n["\r"===n[0]?1:0]}function c(n){return n&&!a(n)}function l(n,e,r){if(!n)return"";n=f.forceComment(n);var o,i=n.length;for(o=0;o<i&&n[o]<=" ";o++);return r&&o>0&&(n=n.substr(o)),o<i?e+t(x.rem,n):n}var g=C(n);if(void 0!==g)return t(x.dsf,g);switch(typeof n){case"string":return i(n,D,e,o);case"number":return isFinite(n)?t(x.num,String(n)):t(x.lit,"null");case"boolean":return t(x.lit,String(n));case"object":if(!n)return t(x.lit,"null");var w;m&&(w=f.getComment(n));var O="[object Array]"===Object.prototype.toString.apply(n),k=D;D+=p;var E,q,S,N,_,I,F,A,L,M,T=h+k,$=h+D,R=r||d?"":T,B=[],W=v?[]:null,U=y,Z=b,H=j?"":x.com[0],z=0;if(O){for(q=0,S=n.length;q<S;q++){if(E=q<S-1,w?(F=w.a[q]||[],A=c(F[1]),B.push(l(F[0],"\n")+$),W&&(F[0]||F[1]||A)&&(W=null)):B.push($),P=0,_=n[q],B.push(s(_,!!w&&A,!0)+(E?j:"")),W){switch(typeof _){case"string":P=0,y=!0,b=0,W.push(s(_,!1,!0)+(E?x.com[0]:"")),y=U,b=Z;break;case"object":if(_){W=null;break}default:W.push(B[B.length-1]+(E?H:""))}E&&(P+=x.com[0].length-x.com[2]),z+=P}w&&F[1]&&B.push(l(F[1],A?" ":"\n",A))}0===S?w&&w.e&&B.push(l(w.e[0],"\n")+T):B.push(T),0===B.length?L=t(x.arr,""):(L=R+t(x.arr,B.join("")),W&&(M=W.join(" "),M.length-z<=v&&(L=t(x.arr,M))))}else{var G=w?w.o.slice():[];for(N in n)Object.prototype.hasOwnProperty.call(n,N)&&G.indexOf(N)<0&&G.push(N);for(q=0,S=G.length;q<S;q++)if(E=q<S-1,N=G[q],w?(F=w.c[N]||[],A=c(F[1]),B.push(l(F[0],"\n")+$),W&&(F[0]||F[1]||A)&&(W=null)):B.push($),P=0,_=n[N],I=s(_,w&&A),B.push(u(N)+x.col[0]+(a(I)?"":" ")+I+(E?j:"")),w&&F[1]&&B.push(l(F[1],A?" ":"\n",A)),W){switch(typeof _){case"string":P=0,y=!0,b=0,I=s(_,!1),y=U,b=Z,W.push(u(N)+x.col[0]+" "+I+(E?x.com[0]:""));break;case"object":if(_){W=null;break}default:W.push(B[B.length-1]+(E?H:""))}P+=x.col[0].length-x.col[2],E&&(P+=x.com[0].length-x.com[2]),z+=P}0===S?w&&w.e&&B.push(l(w.e[0],"\n")+T):B.push(T),0===B.length?L=t(x.obj,""):(L=R+t(x.obj,B.join("")),W&&(M=W.join(" "),M.length-z<=v&&(L=t(x.obj,M))))}return D=k,L}}var f=n("./hjson-common"),c=n("./hjson-dsf"),l={obj:["{","}"],arr:["[","]"],key:["",""],qkey:['"','"'],col:[":",""],com:[",",""],str:["",""],qstr:['"','"'],mstr:["'''","'''"],num:["",""],lit:["",""],dsf:["",""],esc:["\\",""],uni:["\\u",""],rem:["",""]},h=f.EOL,p="  ",m=!1,d=!1,g=!1,y=!1,v=0,b=1,j="",w=null,x=l;if(r&&"object"==typeof r){r.quotes="always"===r.quotes?"strings":r.quotes,"\n"!==r.eol&&"\r\n"!==r.eol||(h=r.eol),m=r.keepWsc,v=r.condense||0,d=r.bracesSameLine,g="all"===r.quotes||"keys"===r.quotes,y="all"===r.quotes||"strings"===r.quotes||r.separator===!0,b=y||"off"==r.multiline?0:"no-tabs"==r.multiline?2:1,j=r.separator===!0?x.com[0]:"",w=r.dsf,"number"==typeof r.space?p=new Array(r.space+1).join(" "):"string"==typeof r.space&&(p=r.space),r.colors===!0&&(x={obj:["[37m{[0m","[37m}[0m"],arr:["[37m[[0m","[37m][0m"],key:["[33m","[0m"],qkey:['[33m"','"[0m'],col:["[37m:[0m",""],com:["[37m,[0m",""],str:["[37;1m","[0m"],qstr:['[37;1m"','"[0m'],mstr:["[37;1m'''","'''[0m"],num:["[36;1m","[0m"],lit:["[36m","[0m"],dsf:["[37m","[0m"],esc:["[31m\\","[0m"],uni:["[31m\\u","[0m"],rem:["[35m","[0m"]});var O,k=Object.keys(l);for(O=k.length-1;O>=0;O--){var E=k[O];x[E].push(l[E][0].length,l[E][1].length)}}var C,q="-­؀-؄܏឴឵‌-‏\u2028- ⁠-⁯\ufeff￰-￿",S=new RegExp('[\\\\\\"\0-'+q+"]","g"),N=new RegExp("^\\s|^\"|^'|^#|^\\/\\*|^\\/\\/|^\\{|^\\}|^\\[|^\\]|^:|^,|\\s$|[\0-"+q+"]","g"),_=new RegExp("'''|^[\\s]+$|[\0-"+(2===b?"\t":"\b")+"\v\f-"+q+"]","g"),I=new RegExp("^(true|false|null)\\s*((,|\\]|\\}|#|//|/\\*).*)?$"),F={"\b":"b","\t":"t","\n":"n","\f":"f","\r":"r",'"':'"',"\\":"\\"},A=/[,\{\[\}\]\s:#"']|\/\/|\/\*/,D="",P=0;C=c.loadDsf(w,"stringify");var L="",M=m?M=(f.getComment(e)||{}).r:null;return M&&M[0]&&(L=M[0]+"\n"),L+=s(e,null,!0,!0),M&&(L+=M[1]||""),L}},{"./hjson-common":2,"./hjson-dsf":3}],6:[function(n,e,r){e.exports="3.1.0"},{}],7:[function(n,e,r){/*!
 * Hjson v3.1.0
 * http://hjson.org
 *
 * Copyright 2014-2017 Christian Zangl, MIT license
 * Details and documentation:
 * https://github.com/hjson/hjson-js
 *
 * This code is based on the the JSON version by Douglas Crockford:
 * https://github.com/douglascrockford/JSON-js (json_parse.js, json2.js)
 */
"use strict";var t=n("./hjson-common"),o=n("./hjson-version"),i=n("./hjson-parse"),a=n("./hjson-stringify"),u=n("./hjson-comments"),s=n("./hjson-dsf");e.exports={parse:i,stringify:a,endOfLine:function(){return t.EOL},setEndOfLine:function(n){"\n"!==n&&"\r\n"!==n||(t.EOL=n)},version:o,rt:{parse:function(n,e){return(e=e||{}).keepWsc=!0,i(n,e)},stringify:function(n,e){return(e=e||{}).keepWsc=!0,a(n,e)}},comments:u,dsf:s.std}},{"./hjson-comments":1,"./hjson-common":2,"./hjson-dsf":3,"./hjson-parse":4,"./hjson-stringify":5,"./hjson-version":6}],8:[function(n,e,r){},{}]},{},[7])(7)});</script>
    <script type="application/javascript" async
>
/* importing gereco.js */
// jshint browser:true, devel: true

(function() {
    window.addEventListener("load", function() {
        var base = document.getElementsByTagName("base")[0],
            addressbar = document.getElementById("addressbar"),
            methodCombo = document.getElementById("method"),
            methodInput = methodCombo.children[0],
            methodSelect = methodCombo.children[1],
            ctypeCombo = document.getElementById("ctype"),
            ctypeInput = ctypeCombo.children[0],
            ctypeSelect = ctypeCombo.children[1],
            send = document.getElementById("send"),
            payload = document.getElementById("payload"),
            response = document.getElementById("response"),
            loading = document.getElementById("loading"),
            responseHeaders = document.getElementById("response-headers"),
            hjsonToolbar = document.getElementById("hjson-toolbar"),
            tohjson = document.getElementById("tohjson"),
            fromhjson = document.getElementById("fromhjson"),
            etag = null,
            req = null,
            enhancing = null;

        // define functions

        function updateCombo(evt) {
            var select = evt.target;
            var input = evt.target.parentNode.children[0];
            var val = select.selectedOptions[0].value;
            if (val === "custom") {
                input.disabled = false;
                input.focus();
            } else {
                input.value = val;
                input.disabled = true;
            }
            if (evt.target === methodSelect) {
                payload.disabled = (val === "GET" || val === "DELETE");
                if (val === "PUT") {
                    payload.value = response.textContent;
                }
            }
        }

        function enhanceContent(elements, ctype, i) {
            enhancing = null;
            if (i < elements.length) {
                var elt = elements[i];
                var html = elt.innerHTML;
                if (/json/.test(ctype) || /html/.test(ctype) || /xml/.test(ctype)) {
                    html = html.replace(/""/g, '<a href="">""</a>');
                    html = html.replace(/"([^">\n]+)"/g, '"<a href="$1">$1</a>"');
                } else if (/text\/uri-list/.test(ctype)) {
                    html = html.replace(/^.*$/gm, '<a href="$&">$&</a>');
                } else {
                    html = html.replace(/&lt;&gt;/g, '<a href="">&lt;&gt;</a>');
                    html = html.replace(/&lt;([^\n]+?)&gt;/g, '&lt;<a href="$1">$1</a>&gt;');
                }
                elt.innerHTML = html;
                enhancing = setTimeout(enhanceContent.bind(self, elements, ctype, i+1), 0);
            }
        }

        function updateCtypeSelect(newCtype) {
            var options = ctypeSelect.children;
            for(var i=0; i<options.length; i++) {
                if (options[i].value === newCtype) {
                    ctypeSelect.selectedIndex = i;
                    break;
                } else if (options[i].value === "custom") {
                    ctypeSelect.selectedIndex = i;
                    ctypeInput.value = newCtype;
                }
            }
            updateCombo({ target: ctypeSelect });
        }


        function sendRequest(evt) {
            if (!evt) evt = {};
            if (evt.forceget) {
                // unless ran as the Send event handler, force GET
                methodSelect.selectedIndex = 0;
                updateCombo({ target: methodSelect });
            }
            if (req !== null) {
                req.abort();
                console.log("aborting previous request");
            }
            req = new XMLHttpRequest(),
                method = methodInput.value || "GET",
                url = addressbar.value;
            base.href = addressbar.value;
            url = url.split("#", 1)[0];
            if (method === "GET" || method === "HEAD") {
                // use JQuery hack to prevent cache
                var uncache = "_=" + Number(new Date());
                if (/\?/.test(addressbar.value)) {
                    url += "&" + uncache;
                } else {
                    url += "?" + uncache;
                }
            }
            req.withCredentials = true;
            req.open(method, url);

            var accept = "application/json;q=0.8,*/*;q=0.1";
            if (sessionStorage.lastAcceptedCType) {
                accept = sessionStorage.lastAcceptedCType + ';q=0.9,' + accept;
            }
            if (ctypeInput.value && ctypeInput.value !== '*/*') {
                sessionStorage.lastAcceptedCType = ctypeInput.value;
                accept = ctypeInput.value + ',' + accept;
            }
            req.setRequestHeader("accept", accept);

            if (method !== "GET") {
                req.setRequestHeader("content-type", ctypeInput.value);
            }
            if (method === "PUT" || method === "DELETE") {
                if (etag) {
                    req.setRequestHeader("if-match", etag);
                }
            }
            if (!evt.poppingState && String(window.location) !== addressbar.value) {
                try {
                    window.history.pushState({}, addressbar.value, addressbar.value);
                }
                catch(err) {
                    if (err.name !== "SecurityError") throw err;
                    // if this is just a SecurityError, then pushState with "safe" URL
                    var newUrl = String(window.location).split("#", 1)[0];
                    newUrl += "#" + addressbar.value ;
                    window.history.pushState({}, newUrl, newUrl);
                }
            }
            if (enhancing !== null) {
                //clearTimeout(enhancing);
            }
            response.textContent = "";
            response.classList.remove("error");
            response.classList.add("loading");
            response.appendChild(loading);
            responseHeaders.innerHTML = "";
            var oldLength = 0;
            var ctype;
            var remaining = "";

            req.onreadystatechange = function() {
                if (req.readyState === 2) {
                    //console.log("received header");

                    // display response headers
                    req.getAllResponseHeaders().split("\n").forEach(function(rh) {
                        if (!rh) return;
                        var match = /([^:]+): *(.*)/.exec(rh);
                        var key = match[1];
                        var val = match[2];

                        var row = responseHeaders.appendChild(document.createElement("tr"));
                        var th = row.appendChild(document.createElement("th"));
                        var td = row.appendChild(document.createElement("td"));

                        th.textContent = key;

                        // custom presentation of some header fields
                        if (/location/i.test(key)) {
                            var linka = td.appendChild(document.createElement("a"));
                            linka.href = val;
                            linka.textContent = val;
                        } else if (/link/i.test(key)) {
                            makeLinksIn(td, val);
                        } else {
                            td.textContent = val;
                        }
                    });

                    // additional processing of some response headers
                    if (Math.floor(req.status / 100) === 2) {
                        // etag
                        etag = req.getResponseHeader("etag");

                        // content-type
                        ctype = req.getResponseHeader("content-type");
                        if (ctype) {
                            updateCtypeSelect(ctype.split(";", 1)[0]);
                        }
                    }
                } else if (req.readyState >= 3) {
                    //console.log("received content part: " + req.responseText.substr(oldLength));
                    remaining += req.responseText.substr(oldLength);
                    oldLength = req.responseText.length;
                    var lines = remaining.split('\n');
                    if (lines.length && remaining[-1] !== '\n') {
                        remaining = lines.pop(-1);
                    } else {
                        remaining = "";
                    }
                    for (var i=0; i<lines.length; i+=1) {
                        var line = lines[i];
                        var span = document.createElement('span');
                        span.textContent = line + '\n';
                        response.appendChild(span);
                    }

                    if (req.readyState === 4) {
                        //console.log("received end of response");
                        if (remaining) {
                            var span = document.createElement('span');
                            span.textContent = remaining;
                            response.appendChild(span);
                        }
                        response.classList.remove("loading");
                        response.removeChild(loading);
                        document.title = "REST Console - " + addressbar.value;
                        enhanceContent(response.children, ctype, 0);
                        if (Math.floor(req.status / 100) === 2) {
                            response.classList.remove("error");
                            if (req.getResponseHeader("content-type").startsWith('x-gereco') &&
                                  // only trust x-gereco/* mime-types if they come from the same server
                                  addressbar.value === window.location.toString()) {
                                var iframe = document.createElement('iframe');
                                iframe.seamless = true;
                                iframe.scrolling = "no";
                                iframe.onload = function() {
                                    var ifdoc = iframe.contentDocument;
                                    iframe.style.height = (ifdoc.body.scrollHeight+32) + 'px';
                                    iframe.style.width = (ifdoc.body.scrollWidth+32) + 'px';
                                    var theme = document.querySelector('style#theme');
                                    ifdoc.head.insertBefore(
                                        theme.cloneNode(true),
                                        ifdoc.head.children[0]
                                    );

                                    ifdoc.body.addEventListener("click", interceptLinks);
                                };
                                iframe.srcdoc = req.responseText;
                                response.textContent = "";
                                response.appendChild(iframe);
                            }
                        } else {
                            response.classList.add("error");
                            if (req.statusText) {
                                response.textContent =
                                    req.status + " " + req.statusText + "\n\n" +
                                    req.responseText;
                            } else {
                                response.textContent = "Can not reach " + addressbar.value;
                            }
                        }
                        req = null;
                        }
                }
            };
            if (payload.disabled) req.send();
            else req.send(payload.value);
        }

        function interceptLinks (evt) {
            if (evt.target.nodeName === "A" &&
                  !evt.ctrlKey &&
                  (!evt.target.target || evt.target.target === '_self')) {
                evt.preventDefault();
                addressbar.value = evt.target.href;
                sendRequest({ forceget: true });
            }
        }

        function updateAddressBar() {
            if (window.location.hash) {
                addressbar.value = window.location.hash.substr(1);
            } else {
                addressbar.value = window.location;
            }
        }

        function makeLinksIn(td, links) {
          var ul = td.appendChild(document.createElement("ul"));
          var li = null;
          // the split below is not absolutely robust, but it should work in most cases
          for (link of links.substr(1).split(/, *</)) {
            if (li) { li.appendChild(document.createTextNode(",")); }
            li = ul.appendChild(document.createElement("li"));
            li.appendChild(document.createTextNode("<"));
            var cutpoint = link.search(">");
            var url = link.substr(0, cutpoint);
            var a = li.appendChild(document.createElement("a"));
            a.href = url;
            a.textContent = url;
            li.appendChild(document.createTextNode(link.substr(cutpoint)));
          }
        }

        // add event listeners

        window.addEventListener("popstate", function(e) {
            updateAddressBar();
            sendRequest({ forceget: true, poppingState: true });
        });

        window.addEventListener("keydown", function(evt) {
            if (evt.keyCode === 13 && evt.ctrlKey) { // ctrl+enter
                sendRequest();
            }
        });

        addressbar.addEventListener("keypress", function(evt) {
            if (evt.keyCode === 13) { // enter
                sendRequest({ forceget: true });
            }
        });

        payload.addEventListener("keydown", function(evt) {
            if (evt.keyCode === 9) { // tab
                // TODO insert  "   " properly
                evt.preventDefault();
            }
        });


        methodSelect.addEventListener("change", updateCombo);
        ctypeSelect.addEventListener("change", updateCombo);
        send.addEventListener("click", sendRequest);
        response.addEventListener("click", interceptLinks);
        responseHeaders.addEventListener("click", interceptLinks);

        // H-Json

        function checkHjson() {
            console.debug("checkHjson");
            if (ctypeInput.value.search(/json/) != -1 && !payload.disabled) {
                hjsonToolbar.style.display = "inline-block";
            } else {
                hjsonToolbar.style.display = "none";
            }
        }

        ctypeInput.addEventListener('input', checkHjson);
        ctypeSelect.addEventListener('change', checkHjson);
        methodInput.addEventListener('input', checkHjson);
        methodSelect.addEventListener('change', checkHjson);

        tohjson.addEventListener("click", function(evt) {
            var data = Hjson.parse(payload.value);
            payload.value = Hjson.stringify(data);
        });

        fromhjson.addEventListener("click", function(evt) {
            var data = Hjson.parse(payload.value);
            payload.value = JSON.stringify(data, null, 2);
        });

        // do immediately on load

        updateAddressBar();
        updateCombo({ target: methodSelect });
        updateCombo({ target: ctypeSelect });
        sendRequest({ forceget: true });

    });
})();
</script>

  </body>
</html>
"""
