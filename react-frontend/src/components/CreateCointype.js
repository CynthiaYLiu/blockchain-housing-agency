import React, { Component } from "react";
import ReactDOM from 'react-dom'
import axios from 'axios'

const axiosConfigGet = {
  method: "get",
}
const axiosConfigPost = {
  method: "post",
  url: "http://127.0.0.1:5000/post"
}

class CreateCointype extends Component {
  constructor(props) {
    super(props);
    this.state = {
      cointype: '',
      status:''
    };

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({
      [event.target.id]: event.target.value,
    })
  }

  handleSubmit = () => {
    axios({ ...axiosConfigGet, url: `http://127.0.0.1:5000/actions/cct/${this.state.cointype}` })
      .then((res) => {
        console.log(`response from the server is ${res}`)
        this.setState((prevState) => ({ ...prevState, status: res.data.status }))
      })
      .catch((err) => {
        console.log(`error connecting the server is ${err}`)
      })
  }

  render() {
    return (
      <div>
        <br />
        <h1 className="display-4 text-center mt-4"> Create a New Type of Coin! </h1>
        <h3 className="lead text-center"> 創造新的幣別！</h3>
        <br />
        <label htmlFor="tags">Cointype : </label>
        <input
          type="text"
          className="form-control"
          id="cointype"
          placeholder="Type of the coin"
          value={this.state.cointype}
          onChange={this.handleChange}
          required
        />
        <br /><br />
        <button onClick={this.handleSubmit}>submit</button>
        <br /><br />
        <h2>{this.state.status}</h2>
      </div>
      
    )
  }
}

export default CreateCointype;